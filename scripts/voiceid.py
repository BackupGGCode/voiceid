#!/usr/bin/env python
#############################################################################
#
# VoiceID, Copyright (C) 2011, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it, michela.fancello@crs4.it, 
#        mauro.mereu@crs4.it
# Web: http://code.google.com/p/voiceid
# Authors: Michela Fancello, Mauro Mereu
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#############################################################################
"""
VoiceID is a speaker recognition/identification system written in Python,
based on the `LIUM Speaker Diarization <http://lium3.univ-lemans.fr/diarization/doku.php>`_ framework.

VoiceID can process video or audio files to identify in which slices of 
time there is a person speaking (diarization); then it examines all those
segments to identify who is speaking. To do so you must have a voice models
database. 

To create the database you have to do a "train phase", in
interactive mode, by assigning a label to the "unknown" speakers.
You can also build yourself the speaker models and put in the db
using the scripts to create the gmm files.

"""
import os
import subprocess
import time
import re
import struct
import shutil
import shlex
from optparse import OptionParser
from multiprocessing import cpu_count
from threading import Thread

#-------------------------------------
# initializations and global variables
#-------------------------------------

# http://lium3.univ-lemans.fr/diarization/doku.php
lium_jar = os.path.expanduser('~/.voiceid/lib/LIUM_SpkDiarization-4.7.jar')  
ubm_path  = os.path.expanduser('~/.voiceid/lib/ubm.gmm')
test_path  = os.path.expanduser('~/.voiceid/test')
db_dir = os.path.expanduser('~/.voiceid/gmm_db')
gender_gmms = os.path.expanduser('~/.voiceid/lib/gender.gmms')
sms_gmms = os.path.expanduser('~/.voiceid/lib/sms.gmms')
output_format = 'srt' #default output format
quiet_mode = False

verbose = False
keep_intermediate_files = False

output_redirect = open('/dev/null','w')
if verbose:
        output_redirect = open('/dev/stdout','w')
#        output_redirect = None

#-------------------------------------
#   classes
#-------------------------------------
class VoiceDB:
    """A class that represent a generic voices db.
    
    :param path: the voice db path"""
    def __init__(self, path):
        """        
        :type path: string
        :param path: the voice db path
        """
        self._path = path
        self._genders = ['F', 'M', 'U']
        self._read_db()

    def get_path(self):
        """Get the base path of the voices db, where are stored the voice model 
        files, splitted in 3 directories according to the gender (F, M, U)."""
        return self._path
    
    def get_speakers(self):
        """Return a dictionary where the keys are the genders and the values 
        are a list for every gender with the available speakers models."""
        pass
    
    def _read_db(self):
        pass
    
    def add_model(self, basefilename, speaker_name, gender=None):
        """
        Add a voice model to the database.
        
        :type basefilename: string
        :param basefilename: basename including absolulute path of the voice file
        
        :type speaker_name: string
        :param speaker_name: name or label of the speaker voice in the model, in a single word without special characters
        
        :type gender: char F, M or U
        :param gender: the gender of the speaker in the model 
        """
        pass
    
    def remove_model(self, mfcc_file, speaker_name, value, gender):
        """
        Remove a speaker model from the database according to the score it gets
        by matching vs the given feature file 
        
        :type mfcc_file: string
        :param mfcc_file: the feature(mfcc) file extracted from the wave
        
        :type speaker_name: string
        :param speaker_name: the name or label of the speaker
        
        :type value: float 
        :param value: the score obtained in the voice matching
        
        :type gender: char F, M or U
        :param gender: the speaker gender 
        """
        pass 
    
    def match_voice(self, mfcc_file, speaker_name, gender):
        """
        Match the given feature file vs the specified speaker model.

        :type mfcc_file: string         
        :param mfcc_file: the feature(mfcc) file extracted from the wave
        
        :type speaker_name: string
        :param speaker_name: the name or label of the speaker
        
        :type gender: char F, M or U
        :param gender: the speaker gender 
        """
        pass
    
    def voice_lookup(self, mfcc_file, gender):
        """
        Look for the best matching speaker in the db for the given features file. 
        
        :type mfcc_file: string         
        :param mfcc_file: the feature(mfcc) file extracted from the wave
        
        :type gender: char F, M or U
        :param gender: the speaker gender 
        """
        pass 
    
class GMMVoiceDB(VoiceDB):
    """A Gaussian Mixture Model voices database.
    
    :type path: string         
    :param path: the voice db path"""    
    
    def __init__(self, path, thrd_n=1):
        VoiceDB.__init__(self, path)
        if not hasattr(self, '__threads') :
            self.__threads = {} #class field
        self.__maxthreads = thrd_n
    
    def set_maxthreads(self, t):
        """Set the max number of threads running together.
        
        :type t: integer
        :param t: max number of threads allowed to run at the same time.
        """
        if t > 0:
            self.__maxthreads = t
    
    def _read_db(self):
        """Read for any changes the db voice models files."""
        self._speakermodels = {}
        for g in self._genders:
            self._speakermodels[g] = [ f 
                  for f in os.listdir(os.path.join(self._path, g)) 
                  if f.endswith('.gmm') ]
    
    def add_model(self, basefilename, speaker_name, gender=None):
        """Add a gmm model to db.
        
        :type basefilename: string
        :param basefilename: the wave file basename and path

        :type speaker_name: string
        :param speaker_name: the speaker in the wave

        :type gender: char F, M or U
        :param gender: the gender of the speaker (optional)"""
                
        extract_mfcc(basefilename)
        
        ensure_file_exists(basefilename+".mfcc")
        build_gmm(basefilename, speaker_name)
#        try:
#            _silence_segmentation(basefilename)
#        except:
#            return False
        if gender == None:
            def _get_gender_from_seg(segfile):
                g = {'M':0, 'F':0, 'U':0}
                f = open(segfile, 'r')
                for l in f.readlines():
                    if not l.startswith(';;'):
                        g[ l.split(' ')[4] ] +=1
                f.close()    
                
                if g['M'] > g['F']:
                    return 'M'
                elif g['M'] < g['F']: 
                    return 'F'
                else: 
                    return 'U'
            gender = _get_gender_from_seg(basefilename + '.seg')
                
#            _gender_detection(basefilename)
#        else:
#            shutil.move(basefilename + '.s.seg', basefilename + '.seg')
#        ident_seg(basefilename, speaker_name)
#        _train_init(basefilename)
#        extract_mfcc(basefilename)
#        _train_map(basefilename)
        
        gmm_path = basefilename + '.gmm'
        orig_gmm = os.path.join(self.get_path(), 
                                    gender, speaker_name + '.gmm')
        try:
            ensure_file_exists(orig_gmm)
            merge_gmms([orig_gmm, gmm_path], orig_gmm)
            self._read_db()
            return True
        except Exception,e:
            s = "File %s doesn't exist or not correctly created" % orig_gmm
            if str(e) == s:
                shutil.move(gmm_path, orig_gmm)
                self._read_db()
                return True
        return False
    
    def remove_model(self, mfcc_file, speaker_name, value, gender):
        """Remove a voice model from the db.

        :type mfcc_file: string
        :param mfcc_file: the mfcc file name and path
        
        :type speaker_name: string
        :param speaker_name: the speaker in the wave
        
        :type value: float
        :param value: the value of

        :type gender: char F, M or U         
        :param gender: the gender of the speaker (optional)"""
        old_s = speaker_name
        
        folder_db_dir = os.path.join(self.get_path(),gender)
        
        if os.path.exists(os.path.join(folder_db_dir, old_s + ".gmm")):
            folder_tmp = os.path.join(folder_db_dir, old_s + "_tmp_gmms")
            if not os.path.exists(folder_tmp):
                os.mkdir(folder_tmp)
                
            split_gmm(os.path.join(folder_db_dir, old_s + ".gmm"), 
                      folder_tmp)
            listgmms = os.listdir(folder_tmp)
            filebasename = os.path.splitext(mfcc_file)[0]
            value_old_s = value
            
            if len(listgmms) != 1:
                for gmm in listgmms:
                    mfcc_vs_gmm(filebasename, 
                                os.path.join(old_s + "_tmp_gmms", gmm), 
                                gender)
                    f = open("%s.ident.%s.%s.seg" % 
                             (filebasename, gender, gmm), "r")
                    for l in f:
                        if l.startswith(";;"):
                            s_name = l.split()[1].split(':')[1].split('_')[1]
                            i = l.index('score:' + s_name) + len('score:' 
                                                                 + s_name 
                                                                 + " = ")
                            ii = l.index(']', i) - 1
                            value_tmp = l[i:ii]
                            if float(value_tmp) == value_old_s:
                                os.remove(os.path.join(folder_tmp, gmm))
                merge_gmms(listgmms, 
                           os.path.join(folder_db_dir, old_s + ".gmm"))
            else:
                os.remove(os.path.join(folder_db_dir, old_s + ".gmm")) 
            shutil.rmtree(folder_tmp)
            self._read_db()
             
    def match_voice(self, mfcc_file, speaker_name, gender):
        """Match the voice (mfcc file) versus the gmm model of 
        'speaker_name' in db.
        
        :type mfcc_file: string
        :param mfcc_file: the feature(mfcc) file extracted from the wave

        :type speaker_name: string
        :param speaker_name: the speaker in the wave
        
        :type gender: char F, M or U         
        :param gender: the gender of the speaker (optional)"""
        
        mfcc_basename = os.path.splitext(mfcc_file)[0]
                
        mfcc_vs_gmm( mfcc_basename , speaker_name + '.gmm', 
                     gender, self.get_path() )
        cls = {}
        manage_ident( mfcc_basename, 
                      gender + '.' + speaker_name + '.gmm', cls )
        s = {}
        for c in cls:
            s.update( cls[ c ].speakers )
        return s
    
    def get_speakers(self):
        """Return a dictionary where the keys are the genders and the values
        are a list of the available speakers models for every gender."""
        result = {}
        for g in self._genders:
            result[g] = [ os.path.splitext(m)[0] 
                         for m in self._speakermodels[g] ]
        return result
    
    def voice_lookup(self, mfcc_file, gender):
        """Look for the best matching speaker in the db for the given features file. 
        
        :type mfcc_file: string
        :param mfcc_file: the feature(mfcc) file extracted from the wave

        :type gender: char F, M or U         
        :param gender: the speaker gender 
        """
        speakers =  self.get_speakers()[gender]
        res = {}
        out = {}
        
        def match_voice(self, mfcc_file, speaker, gender, output):
            out[speaker+mfcc_file+gender] = self.match_voice(mfcc_file, speaker, gender)
        
        keys = []
        
        for s in speakers:
            out[s+mfcc_file+gender] = None
            if  alive_threads(self.__threads)  < self.__maxthreads :
                keys.append(s+mfcc_file+gender)
                self.__threads[s+mfcc_file+gender] = Thread(target=match_voice, 
                                      args=(self, mfcc_file, s, gender, out[s+mfcc_file+gender] ) )
                self.__threads[s+mfcc_file+gender].start()
            else:
                while alive_threads(self.__threads) >= self.__maxthreads:
                    time.sleep(1)
                keys.append(s+mfcc_file+gender)
                self.__threads[s+mfcc_file+gender] = Thread(target=match_voice, 
                                      args=(self, mfcc_file, s, gender, out[s+mfcc_file+gender] ) )
                self.__threads[s+mfcc_file+gender].start()                
            
        for thr in keys:
            if self.__threads[thr].is_alive():
                self.__threads[thr].join()
            res.update( out[thr] )    
            
        return res

class Segment:
    """A Segment taken from a segmentation file, representing the smallest recognized
     voice time slice.

    :type line: string
    :param line: the line taken from a seg file
    """
    
    def __init__(self, line):
        """
        :type line: string
        :param line: the line taken from a seg file
        """
        self._basename = str(line[0])
        self._one = int(line[1])
        self._start = int(line[2])
        self._duration = int(line[3])
        self._gender = str(line[4])
        self._environment = str(line[5])
        self._u = str(line[6])
        self._speaker = str(line[7])
        self._line = line[:]

    def get_basename(self):
        return self._basename

    def get_start(self):
        return self._start
    
    def get_end(self):
        return self._start + self._duration 
    
    def get_duration(self):
        return self._duration

    def get_gender(self):
        return self._gender

    def get_environment(self):
        return self._environment

    def get_speaker(self):
        return self._speaker

    def get_line(self):
        return self._line

class Cluster:
    """A Cluster object, representing a computed cluster for a single
    speaker, with gender, a number of frames and environment.

    :type name: string
    :param name: the cluster identifier
    
    :type gender: char F, M or U                   
    :param gender: the gender of the cluster
    
    :type frames: integer
    :param frames: total frames of the cluster
    
    :type dirname: string
    :param dirname: the directory where is the cluster wave file"""

    
    def __init__(self, name, gender, frames, dirname ):
        """
        :type name: string
        :param name: the cluster identifier
        
        :type gender: char F, M or U                   
        :param gender: the gender of the cluster
        
        :type frames: integer
        :param frames: total frames of the cluster
        
        :type dirname: string
        :param dirname: the directory where is the cluster wave file"""
        
        self.gender = gender
        self._frames = frames
        self._e = None #environment (studio, telephone, unknown)
        self._name = name
        self._speaker = None
        self._segments = []
        self._seg_header = None
        self.speakers = {}
        self.up_to_date = True
        self.wave = None
        self.mfcc = None
        self.dirname = dirname
        
    def __str__(self):
        return "%s (%s)" % (self._name, self._speaker)

    def add_speaker(self, name, value):
        """Add a speaker with a computed score for the cluster, if a better 
        value is already present the new value will be ignored.
        
        :type name: string
        :param name: the speaker name
        
        :type value: float
        :param value: score computed between the cluster wave and speaker model
        """
        v = float(value)
        if self.speakers.has_key( name ) == False:
            self.speakers[ name ] = v
        else:
            if self.speakers[ name ] < v:
                self.speakers[ name ] = v

    def get_speaker(self):
        """Set the right speaker for the cluster if not set and returns
         its name."""
        if self._speaker == None:
            self._speaker = self.get_best_speaker()
        return self._speaker
    
    def set_speaker(self, speaker):
        """Set the cluster speaker 'by hand'.
        
        :type speaker: string
        :param speaker: the speaker name or identifier 
        """
        self.up_to_date = False
        self._speaker = speaker

    def get_mean(self):
        """Get the mean of all the scores of all the tested speakers for
         the cluster."""
        return sum(self.speakers.values()) / len(self.speakers) 

    def get_name(self):
        """Get the cluster name assigned by the diarization process."""
        return self._name

    def get_best_speaker(self):
        """Get the best speaker for the cluster according to the scores.
         If the speaker's score is lower than a fixed threshold or is too
         close to the second best matching voice, 
         then it is set as "unknown"."""
        max_val = -33.0
        try:
            self.value = max(self.speakers.values())
        except:
            self.value = -100
        self._speaker = 'unknown'
        distance = self.get_distance()
        if self.value > max_val - distance:
            for s in self.speakers:
                if self.speakers[s] == self.value:
                    self._speaker = s
                    break
        if distance < .09:
            self._speaker = 'unknown'
        return self._speaker
    
    def get_best_five(self):
        """Return an array of five most probable speakers represented by 
        ordered tuples of the form (speaker, score) ordered by score."""
        return sorted(self.speakers.iteritems(), key=lambda (k,v): (v,k),
                      reverse=True)[:5]
    
    def get_gender(self):
        """Get the computed gender of the Cluster."""
        g = {'M':0, 'F':0, 'U':0}
        differ = False
        for s in self._segments:
            gg = s.get_gender()
            if gg != self.gender:
                differ = True
                g[gg] += s.get_duration()
                
        if differ:
            if g['M'] > g['F']:
                return 'M'
            else: 
                return 'F'
        else:
            return self.gender  

    def get_distance(self):
        """Get the distance between the best speaker score and the closest
        speaker score."""
        values = self.speakers.values()
        values.sort(reverse=True)
        try:
            return abs(values[1]) - abs(values[0])
        except:
            return 1000.0

    def get_m_distance(self):
        """Get the distance between the best speaker score and the mean of
        all the speakers' scores.""" 
        value = max(self.speakers.values())
        return abs( abs(value) - abs(self.get_mean()) )

    def generate_seg_file(self, filename):
        """Generate a segmentation file for the cluster.
        
        :type filename: string
        :param filename: the name of the seg file
        """
        self._generate_a_seg_file(filename, self.wave[:-4])

    def _generate_a_seg_file(self, filename, name):
        """Generate a segmentation file for the given showname.

        :type filename: string
        :param filename: the name of the seg file
        
        :type name: string
        :param name: the name in the first column of the seg file,
               in fact the name and path of the corresponding wave file
        """
        f = open(filename, 'w')
        f.write(self._seg_header)
        line = self._segments[0].get_line()
        line[0] = name
        line[2] = 0
        line[3] = self._frames - 1
        f.write("%s %s %s %s %s %s %s %s\n" % tuple(line) )
        f.close()
        
    def merge_waves(self, dirname):
        """Take all the wave of a cluster and build a single wave.

        :type dirname: string
        :param dirname: the output dirname
        """        
        name = self.get_name() 
        videocluster =  os.path.join(dirname, name)
        
        listwaves = os.listdir(videocluster)
        
        listw = [ os.path.join(videocluster, f) for f in listwaves ]
        
        file_basename = os.path.join(dirname, name)
        
        self.wave = os.path.join(dirname, name + ".wav")
        
        merge_waves(listw, self.wave)      
        try:
            ensure_file_exists(file_basename + '.mfcc')
        except Exception:
            extract_mfcc(file_basename)
            
    def to_dict(self):
        """A dictionary representation of a Cluster."""
        speaker = self.get_speaker()
        segs = []
        for s in self._segments:
            t = s._line[2:]
            t[-1] = speaker
            t[0] = int(t[0])
            t[1] = int(t[1])
            t.append(self.get_name()) 
            segs.append(t)
        return segs
    
    def print_segments(self):
        """Print cluster timing."""
        for s in self._segments:
            print "%s to %s" % ( humanize_time( float(s.get_start()) / 100 ),
                                 humanize_time( float(s.get_end()) / 100 ) )

class Voiceid:
    """The main object that represents the file audio/video to manage.
        
    :type db: object
    :param db: the VoiceDB database instance
    
    :type filename: string
    :param filename: the wave or video file to be processed
    
    :type single: boolean
    :param single: set to True to force to avoid diarization (a faster 
           approach) only in case you have just a single speaker in the file      
    """

#    @staticmethod 
#    def from_dict(db, json_dict):
#        """Build a Voiceid object from json dictionary. 
#        :param json_dict the json style python dictionary representing
#               a Voiceid object instance
#        """
#        v = Voiceid(db, json_dict['url'])
#        dirname = os.path.splitext(json_dict['url'])
#        
#        for e in json_dict['selections']:            
#            c = v.get_cluster(e['speakerLabel'])
#            if not c:
#                c = Cluster(e['speaker'], e['gender'], 0, dirname)
#            s = Segment([dirname, 1, int(e['startTime'] * 100), 
#                         int( 100 * (e['endTime'] - e['startTime']) ), 
#                         e['gender'], 'U', 'U', e['speaker'] ])
#            c._segments.append(s)
#            v.add_update_cluster(e['speakerLabel'], c)
#        return v

    def __init__(self, db, filename, single=False ):
        """ 
        :type db: object
        :param db: the VoiceDB database instance
        
        :type filename: string
        :param filename: the wave or video file to be processed
        
        :type single: boolean
        :param single: set to True to force to avoid diarization (a faster 
               approach) only in case you have just a single speaker in the file         
        """
        self.status_map = {0:'file_loaded', 1:'file_converted', 
                           2:'diarization_done', 3:'trim_done', 
                           4:'mfcc extracted', 5:'speakers matched'} 
        self.working_map = {0:'converting_file', 1:'diarization',
                            2:'trimming', 3:'mfcc extraction',
                            4:'voice matching', 5:'extraction finished'}
        self._clusters = {}
        self._ext = ''       
        self._time = 0
        self._interactive = False 
        self._db = db
        ensure_file_exists(filename)
        self._set_filename(filename)
        self._status = 0
        self._single = single  
            
    def __getitem__(self, key):
        return self._clusters.__getitem__(key)
    
    def __iter__(self):
        """Just iterate over the cluster's dictionary."""
        return self._clusters.__iter__()
    
    def get_status(self):
        return self._status

    def get_working_status(self):
        #TODO: fix some issue on restarting and so on about current status
        return self.working_map[ self.get_status() ]  
    
    def get_db(self):
        return self._db
    
    #setters and getters
    def get_interactive(self):
        return self._interactive

    def set_interactive(self, value):
        self._interactive = value

    def get_clusters(self):
        return self._clusters

    def set_clusters(self, value):
        self._clusters = value

    def get_time(self):
        return self._time

    def set_time(self, value):
        self._time = value
    
    def _set_filename(self, filename):
        """ 
        Set the filename of the current working file
        """
        
        new_file = filename
        new_file = new_file.replace("'",'_').replace('-','_').replace(' ','_')
        try:
            shutil.copy(filename,new_file)
        except shutil.Error, e:
            s = "`%s` and `%s` are the same file" % (filename, new_file)
            if  str(e) == s:
                pass
            else:
                raise e
        ensure_file_exists(new_file)
        
        self._filename = new_file
        self._basename, self._ext = os.path.splitext(self._filename)
        
    def get_filename(self):
        """Get the name of the current working file."""
        return self._filename
        
    def get_file_basename(self):
        """Get the basename of the current working file."""
        return self._basename[:]
    
    def get_file_extension(self):
        """Get the extension of the current working file."""
        return self._ext[:]
        
    def get_cluster(self, identifier):
        """Get a the cluster by a given identifier.
        
        :type identifier: string
        :param identifier: the cluster identifier (i.e. S0, S12, S44...)
        """
        try:
            return self._clusters[ identifier ]
        except:
            return None
    
    def add_update_cluster(self, identifier, cluster):
        """Add a cluster or update an existing cluster.

        :type identifier: string
        :param identifier: the cluster identifier (i.e. S0, S12, S44...)
        
        :type cluster: object
        :param cluster: a Cluster object
        """
        self._clusters[ identifier ] = cluster
        
    def remove_cluster(self, identifier):
        """Remove and delete a cluster. 

        :type identifier: string
        :param identifier: the cluster identifier (i.e. S0, S12, S44...)
        """
        del self._clusters[identifier]
        
    def get_time_slices(self):
        """Return the time slices with all the information about start time,
        duration, speaker name or "unknown", gender and sound quality
        (studio/phone)."""
        tot = []
        for c in self._clusters:
            tot.extend(self._clusters[c].to_dict()[:])
        tot.sort()
        return tot

    def get_speakers_map(self):
        """A dictionary map between speaker label and speaker name."""
        speakers = {}
        for c in self:
            speakers[c] = self[c].get_best_speaker()
        return speakers
    
    def _to_WAV(self):
        """In case the input file is a video or the wave is in a wrong format,
         convert to wave."""
        file2wav(self.get_filename())
        
    def diarization(self):
        """Run the diarization process. In case of single mode (single speaker 
        in the input file) just create the seg file with silence and gender 
        detection."""
        if self._single:
            self._to_MFCC()
            try:
                os.mkdir(self.get_file_basename())
            except Exception,e:
                if e.errno != 17:
                    raise e
            _silence_segmentation(self._basename)
            _gender_detection(self._basename)
            segname = self._basename + '.seg'
            f = open(segname,'r')
            headers = []
            values = []
            
            differ = False
            basic = None
            gg = {'M' : 0, 'F' : 0, 'U' : 0}
            
            for line in f.readlines():
                if line.startswith(';;'):
                    headers.append( line[line.index('['):] )
                else:
                    a = line.split(' ')
                    
                    if basic == None :
                        basic = a[4]
                    if a[4] != basic :
                        differ = True
                    gg[ a[4] ] +=  int(a[ 3 ])

                    values.append( a )
            h = ";; cluster:S0 %s" % headers[0]
            from operator import itemgetter
            index = 0
            while index < len(values):
                values[index][2] = int(values[index][2])
                index += 1
            values = sorted(values, key=itemgetter(2) )
            index = 0
            while index < len(values):
                values[index][2] = str(values[index][2])
                index += 1    
            newfile = open(segname + '.tmp', 'w')
            newfile.write(h)
            
            if differ: #in case the gender of the single segments differ 
                       #then set the prevailing
#                print 'transgender :-D'
                if gg[ 'M' ] > gg[ 'F' ]:
                    basic = 'M'
                elif gg[ 'M' ] < gg[ 'F' ] : 
                    basic = 'F'
                else:
                    basic = 'U' 
                
            for l in values:
                l[4] = basic #same gender for all segs
                newfile.write(' '.join(l[:-1]) + ' S0\n' )
            f.close()
            newfile.close()
            shutil.copy(self.get_file_basename() + '.mfcc', 
                        os.path.join(self.get_file_basename(), 'S0' + '.mfcc'))
            shutil.move(segname + '.tmp', segname)
            shutil.copy(self.get_file_basename() + '.seg', 
                        os.path.join(self.get_file_basename(), 'S0' + '.seg'))
            ensure_file_exists(segname)
        else:
            diarization(self._basename)
        
    def _to_MFCC(self):
        """Extract the mfcc of the wave input file. Needs the wave file so a 
        prerequisite is _to_WAV()."""
        extract_mfcc(self._basename)
    
    def _to_trim(self):
        """Trim the wave input file according to the segmentation in the seg
        file. Run after diarization."""
        seg2trim(self._basename+'.seg')
        
    def _extract_clusters(self):
        extract_clusters(self._basename+'.seg', self._clusters)

    def extract_speakers(self, interactive=False, quiet=False, thrd_n=1):
        """Identify the speakers in the audio wav according to a speakers
        database. If a speaker doesn't match any speaker in the database then
        sets it as unknown. In interactive mode it asks the user to set
        speakers' names.
        
        :type interactive: boolean
        :param interactive: if True the user must interact to give feedback or 
                train the computed clusters voices
                
        :type quiet: boolean
        :param quiet: silent mode, no prints in batch mode
        
        :type thrd_n: integer
        :param thrd_n: max number of concurrent threads for voice db matching 
        """
        
        if thrd_n < 1: thrd_n = 1
        self.get_db().set_maxthreads(thrd_n)
        
        self._status = 0
        start_time = time.time()
        if not quiet: 
            print self.get_working_status()
        self._to_WAV()
        
        self._status = 1    
        
        if not quiet: 
            print self.get_working_status()
        
        self.diarization()
        
        self._status = 2   
        if not quiet: 
            print self.get_working_status()        
        self._to_trim()
        
        self._status = 3  
        if not quiet: 
            print self.get_working_status()
        diarization_time = time.time() - start_time

        self._to_MFCC()
        self._status = 4 
        basename = self.get_file_basename()

        if not quiet: 
            print self.get_working_status()
        self._extract_clusters()
        
        #merging segments wave files for every cluster
        for cluster in self._clusters:
            self[cluster].merge_waves(basename)
            self[cluster].generate_seg_file(os.path.join(basename, 
                                                         cluster + ".seg"))
       
        for cluster in self._clusters:            
            filebasename = os.path.join(basename, cluster)
            results = self.get_db().voice_lookup(filebasename + '.mfcc', 
                                                 self[cluster].gender)
            for r in results:
                self[cluster].add_speaker(r, results[r])
            
        if not quiet: 
            print ""
        speakers = {}
        
        for c in self._clusters:
            if not quiet: 
                print "**********************************"
                print "speaker ", c
                if interactive: self[c].print_segments()
            speakers[c] = self[c].get_best_speaker()
            if not interactive: 
                for speaker in self[c].speakers:
                    if not quiet: 
                        print "\t %s %s" % (speaker, self[c].speakers[speaker])
                if not quiet: 
                    print '\t ------------------------'
                
            distance = self[c].get_distance()
            
            try:
                mean = self[c].get_mean()
                m_distance = self[c].get_m_distance()
            except:
                mean = 0
                m_distance = 0
    
            if interactive == True:
                self.set_interactive( True )
                
                speakers[c] = best = _interactive_training(basename, 
                                                          c, speakers[c])
                self[c].set_speaker(best)
                
            if not interactive:
                if not quiet:
                    print """\t best speaker: %s (distance from 2nd %f - mean %f - distance from mean %f ) """ % (speakers[c],
                                                                                                                  distance, 
                                                                                                                  mean, m_distance)    
        sec = wave_duration( basename+'.wav' )
        total_time = time.time() - start_time
        self.set_time( total_time )
        self._status = 5
        if not quiet: print self.get_working_status()
        if interactive:
            print "Updating db"
            self.update_db(thrd_n)

        if not interactive:
            if not quiet: 
                speakers_in_db = self.get_db().get_speakers()
                tot_voices = len(speakers_in_db['F']) + \
                    len(speakers_in_db['M'])+len(speakers_in_db['U'])
                voice_time = float(total_time - diarization_time ) 
                t_f_s = voice_time / len(speakers_in_db) 
                print """\nwav duration: %s\nall done in %dsec (%s) (diarization %dsec time:%s )  with %s threads and %d voices in db (%f) """ % (humanize_time(sec), 
                                                                                                                                                  total_time, 
                                                                                                                                                  humanize_time(total_time), 
                                                                                                                                                  diarization_time, 
                                                                                                                                                  humanize_time(diarization_time), 
                                                                                                                                                  thrd_n, 
                                                                                                                                                  tot_voices, 
                                                                                                                                                  t_f_s)
            
    def _match_voice_wrapper(self, cluster, mfcc_name, db_entry, gender ):
        """A wrapper to match the voices each in a different Thread."""
        results = self.get_db().match_voice(mfcc_name, db_entry, gender)
        for r in results:
            self[cluster].add_speaker(r, results[r])

    def update_db(self, t_num=4):
        """Update voice db after some changes, for example after a train 
        session.

        :type t_num: integer
        :param t_num: number of contemporary threads processing the update_db  
        """
        def _get_available_wav_basename(speaker, basedir):
            cont = 0
            speaker = os.path.join(basedir, speaker)
            wav_name = speaker + ".wav"
            if os.path.exists(wav_name):
                while True: #search an inexistent name for new gmm
                    cont = cont +1
                    wav_name = speaker + "" + str(cont) + ".wav"
                    if not os.path.exists(wav_name):
                        break
            return speaker + str(cont)
        
        
        def _build_model_wrapper(self, wave_b, cluster, wave_dir, new_speaker, 
                                 old_speaker):
            """ A procedure to wrap the model building to run in a Thread """
            try:
                ensure_file_exists(wave_b+'.seg')
            except:
                self[cluster]._generate_a_seg_file( wave_b+'.seg', wave_b)                             
         
            ensure_file_exists(wave_b+'.wav')
#            new_speaker = self[cluster].get_speaker()
            self.get_db().add_model(wave_b, new_speaker, 
                                    self[cluster].gender )
            self._match_voice_wrapper(cluster, wave_b+'.mfcc', new_speaker, 
                                      self[cluster].gender)                            
            b_s = self[cluster].get_best_speaker()
            
#            print 'b_s = %s   new_speaker = %s ' % ( b_s, new_speaker )
            
            if b_s != new_speaker :
#                print "removing model for speaker %s" % (old_speaker)
                mfcc_name = os.path.join(wave_dir, cluster) + '.mfcc'
                self.get_db().remove_model(mfcc_name, old_speaker, 
                                           self[cluster].value, 
                                           self[cluster].gender )
                self[cluster].set_speaker(new_speaker)
            if not keep_intermediate_files:
                try:
                    os.remove("%s.seg" % wave_b )
                    os.remove("%s.mfcc" % wave_b )
                    os.remove("%s.ident.seg" % wave_b )
                    os.remove("%s.init.gmm" % wave_b )
                    os.remove("%s.wav" % wave_b )
                except:
                    pass
            #end _build_model_wrapper
            
        thrds = {}
        
        for c in self._clusters.values():
            if c.up_to_date == False:
                
                current_speaker = c.get_speaker()
                old_s= c.get_best_speaker()
                if current_speaker != 'unknown' and current_speaker != old_s:
                    b_file = _get_available_wav_basename(current_speaker, os.getcwd())
                    wav_name = b_file + '.wav'
                    basename = self.get_file_basename()
                    c.merge_waves( basename )
                    shutil.move(c.wave, wav_name)
                    
                    cluster_label = c.get_name()
                    thrds[cluster_label] = Thread(target=_build_model_wrapper,
                                                  args=(self, b_file, 
                                                        cluster_label, 
                                                        basename, 
                                                        current_speaker, old_s) )
                    thrds[cluster_label].start()
                c.up_to_date = True
        
        for t in thrds:
            if thrds[t].is_alive():
                thrds[t].join()

    def to_XMP_string(self):
        """Return the Adobe XMP representation of the information about who is
        speaking and when. The tags used are Tracks and Markers, the ones used 
        by Adobe Premiere for speech-to-text information.""" 
        """
        ...
        <xmpDM:Tracks>
            <rdf:Bag>
                <rdf:li>
                    <rdf:Description
                     xmpDM:trackName="Speaker identification">
                        <xmpDM:markers>
                            <rdf:Seq>
                                <rdf:li
                                 xmpDM:startTime="310"
                                 xmpDM:duration="140"
                                 xmpDM:speaker="Speaker0"
                                 />
                                <rdf:li
                                 xmpDM:startTime="450"
                                 xmpDM:duration="60"
                                 xmpDM:speaker="Speaker0"
                                 />
                            </rdf:Seq>
                        </xmpDM:markers>
                    </rdf:Description>
                </rdf:li>
            </rdf:Bag>
        </xmpDM:Tracks>
        ...
        """
        initial_tags = """<?xml version="1.0"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description  xmlns:xmpDM="http://ns.adobe.com/xmp/1.0/DynamicMedia/">
            <xmpDM:Tracks>
                <rdf:Bag>
                    <rdf:li>
                        <rdf:Description
                         xmpDM:trackName="Speaker identification">
                            <xmpDM:markers>
                                <rdf:Seq>"""
        inner_string = '' 
        for s in self.get_time_slices():
            inner_string += """    
                                    <rdf:li
                                     xmpDM:startTime="%s"
                                     xmpDM:duration="%s"
                                     xmpDM:speaker="%s"
                                     /> """ % (s[0], s[1], s[-2] )
        
        final_tags = """
                                </rdf:Seq>
                            </xmpDM:markers>
                        </rdf:Description>
                    </rdf:li>
                </rdf:Bag>
            </xmpDM:Tracks>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>
"""
        #TODO: extract previous XMP information from the media and merge 
        #      with speaker information
        return initial_tags + inner_string + final_tags            

    
    def to_dict(self):
        """Return a JSON representation for the clustering information."""
#        """ The JSON model used is like:
#        <code>
#{
#    "duration": 15,
#    "url": "url1",
#    "selections": [{
#        "annotations": [{
#            "author": "",
#            "description": "speaker",
#            "keyword": "john",
#            "lang": "EN"
#        },
#        {
#            "author": "",
#            "description": "speakerLabel",
#            "keyword": "S0",
#            "lang": "EN"
#        }
#        , {
#            "author": "",
#            "description": "gender",
#            "keyword": "F",
#            "lang": "EN"        
#        }],
#        "resolution": "0x0",
#        "selW": 20,
#        "selH": 15,
#        "selY": 10,
#        "selX": 10,
#        "startTime" : 0,
#        "endTime" : 10
#        
#    }]
#}
#        </code>
#        
#        """
        
        d = {"duration":self._time,
            "url": self._filename,
            "selections": []
            }
        
        for s in self.get_time_slices():
            d['selections'].append({        
                                     "startTime" : float(s[0]) / 100,
                                     "endTime" : float(s[0] + s[1]) / 100,
                                     'speaker': s[-2],
                                     'speakerLabel': s[-1],
                                     'gender': s[2]
                                     })
        return d

    def write_json(self, dictionary=None):
        """Write to file the json dictionary representation of the Clusters."""
        if not dictionary:
            dictionary = self.to_dict()
        prefix = ''
        if self._interactive:
            prefix = '.interactive'
        
        file_json = open(self.get_file_basename() + prefix + '.json', 'w')
        file_json.write(str(dictionary))
        file_json.close()

    def write_output(self, mode):
        """Write to file (basename.extension, for example: myfile.srt) the 
        output of the recognition process.

        :type mode: string
        :param mode: the output format: srt, json or xmp
        """
        
        if mode == 'srt':
            seg2srt(self.get_file_basename() + '.seg')
            srt2subnames(self.get_file_basename(), self.get_speakers_map())
            shutil.move(self.get_file_basename() + '.ident.srt', 
                        self.get_file_basename() + '.srt')
            
        if mode == 'json':
            self.write_json()
        
        if mode == 'xmp':
            file_xmp = open(self.get_file_basename() + '.xmp', 'w')
            file_xmp.write(str(self.to_XMP_string()))
            file_xmp.close()


#-------------------------------------
#  utils
#-------------------------------------
def alive_threads(t):
    """Check how much threads are running and alive in a thread dictionary

    :param t: thread dictionary like  { key : thread_obj, ... }
    """ 
    num = 0
    for thr in t:
        if t[thr].is_alive():
            num += 1
    return num

def start_subprocess(commandline):
    """Start a subprocess using the given commandline and check for correct
    termination.

    :type commandline: string
    :param commandline: the command to run in a subprocess 
    """
    #print commandline
    args = shlex.split(commandline)
    try:
        p = subprocess.Popen(args, stdin=output_redirect, stdout=output_redirect, 
                             stderr=output_redirect)
        retval = p.wait()
    except:
        args = commandline.split(' ')
        p = subprocess.Popen(args, stdin=output_redirect, stdout=output_redirect, 
                             stderr=output_redirect)
        retval = p.wait()        
        
        
    if retval != 0:
        raise Exception("Subprocess %s closed unexpectedly [%s]" % (str(p), 
                                                                    commandline))

def ensure_file_exists(filename):
    """Ensure file exists and is not empty, otherwise raise an Exception.
    
    :type filename: string
    :param filename: file to check 
    """
    if not os.path.exists(filename):
        raise Exception("File %s doesn't exist or not correctly created" % filename)
    if not (os.path.getsize(filename) > 0):
        raise Exception("File %s empty"  % filename)

def check_deps():
    """Check for dependencies."""
    ensure_file_exists(lium_jar)

    dir_m = os.path.join(db_dir, "M")
    dir_f = os.path.join(db_dir, "F")
    dir_u = os.path.join(db_dir, "U")
    ensure_file_exists(ubm_path)
    if not os.path.exists(db_dir):
        raise Exception("No gmm db directory found in %s (take a look to the configuration, db_dir parameter)" % db_dir )
    if os.listdir(db_dir) == []:
        print "WARNING: Gmm db directory found in %s is empty" % db_dir
    if not os.path.exists(dir_m):
        os.makedirs(dir_m)
    if not os.path.exists(dir_f):
        os.makedirs(dir_f)
    if not os.path.exists(dir_u):
        os.makedirs(dir_u)

def humanize_time(secs):
    """Convert seconds into time format.
    
    :type secs: integer
    :param secs: the time in seconds to represent in human readable format 
           (hh:mm:ss) 
    """
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d,%s' % (hours, mins, int(secs), str(("%0.3f" % secs ))[-3:] )

#-------------------------------------
# wave files management
#-------------------------------------
def wave_duration(wavfile):
    """Extract the duration of a wave file in sec.
    
    :type wavfile: string 
    :param wavfile: the wave input file 
    """
    import wave
    w = wave.open(wavfile)
    par = w.getparams()
    w.close()
    return par[3] / par[2]

def merge_waves(input_waves, wavename):
    """Take a list of waves and append them to a brend new destination wave.
     
    :type input_waves: 
    :param input_waves: the wave files list
    :param wavename: the output wave file to be generated
    """
    #if os.path.exists(wavename):
            #raise Exception("File gmm %s already exist!" % wavename)
    waves = [w.replace(" ","\ ") for w in input_waves]
    w = " ".join(waves)
    commandline = "sox " + str(w) + " " + str(wavename)
    start_subprocess(commandline)

def file2wav(filename):
    """Take any kind of video or audio and convert it to a 
    "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, 
    mono 16000 Hz" wave file using gstreamer. If you call it passing a wave it
    checks if in good format, else it converts the wave in the good format.
    
    :param filename: the input audio/video file to convert 
    """
    def is_bad_wave(filename):
        """Check if the wave is in correct format for LIUM."""
        import wave
        par = None
        try:
            w = wave.open(filename)
            par = w.getparams()
            w.close()
        except Exception,e:
            print e
            return True
        if par[:3] == (1,2,16000) and par[-1:] == ('not compressed',):
            return False
        else:
            return True

    name, ext = os.path.splitext(filename)
    if ext != '.wav' or is_bad_wave(filename):
        start_subprocess( "gst-launch filesrc location='" + filename + "' ! decodebin ! audioresample ! 'audio/x-raw-int,rate=16000' ! audioconvert ! 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1' ! wavenc ! filesink location=" + name + ".wav " )
    ensure_file_exists(name + '.wav')

#-------------------------------------
# gmm files management
#-------------------------------------
def merge_gmms(input_files, output_file):
    """Merge two or more gmm files to a single gmm file with more voice models.
    
    :param input_files: the gmm file list to merge
    :param output_file: the merged gmm output file
    """
    num_gmm = 0
    gmms = ''

    for f in input_files:
        try:
            current_f = open(f,'r')
        except:
            continue

        kind = current_f.read(8)
        if kind != 'GMMVECT_' :
            raise Exception('different kinds of models!')

        num = struct.unpack('>i', current_f.read(4) )
        num_gmm += int(num[0])

        all_other = current_f.read()
        gmms += all_other
        current_f.close()

    num_gmm_string = struct.pack('>i', num_gmm)
    new_gmm = open(output_file,'w')
    new_gmm.write( "GMMVECT_" )
    new_gmm.write(num_gmm_string)
    new_gmm.write(gmms)
    new_gmm.close()
    
def get_gender(input_file):
    """Return gender of a given gmm file.
    """
    gmm = open(input_file,'r')

    kind = gmm.read(8)

    num_gmm_string = gmm.read(4)
    num_gmm = struct.unpack('>i', num_gmm_string )

    if num_gmm != (1,):
        print str(num_gmm) + " gmms"
        raise Exception('Loop needed for gmms')

    gmm_1 = gmm.read(8)
    nothing =  gmm.read(4)

    str_len = struct.unpack('>i', gmm.read(4) )
    name = gmm.read(str_len[0])

    gender = gmm.read(1)
    return gender
    
def split_gmm(input_file, output_dir=None):
    """Split a gmm file into gmm files with a single voice model.
    """
    def read_gaussian(f):
        g_key = f.read(8)     #read string of 8bytes kind
        if g_key != 'GAUSS___':
            raise Exception("Error: the gaussian is not of GAUSS___ key  (%s)" % g_key)
        g_id = f.read(4)
        g_length = f.read(4)     #readint 4bytes representing the name length
        g_name = f.read( int( struct.unpack('>i', g_length )[0] )  )
        g_gender = f.read(1)
        g_kind = f.read(4)
        g_dim = f.read(4)
        g_count = f.read(4)
        g_weight = f.read(8)

        dimension = int( struct.unpack('>i', g_dim )[0] )

        g_header = g_key + g_id + g_length + g_name + g_gender + g_kind + g_dim + g_count + g_weight

#        data = ''
        datasize = 0
        if g_kind == FULL:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < dimension :
                    datasize += 1
                    t += 1
        else:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < j+1 :
                    datasize += 1
                    t += 1

        return g_header + f.read(datasize * 8)

    def read_gaussian_container(f):
        #gaussian container
        ck = f.read(8)    #read string of 8bytes
        if ck != "GAUSSVEC":
            raise Exception("Error: the gaussian container is not of GAUSSVEC kind %s" % ck)
        cs = f.read(4)    #readint 4bytes representing the size of the gaussian 
                          #container
        stuff = ck + cs
        for index in range( int( struct.unpack( '>i', cs )[0] ) ):
            stuff += read_gaussian(f)
        return stuff

    def read_gmm(f):
        myfile = {}
        #single gmm

        k = f.read(8)     #read string of 8bytes kind
        if k != "GMM_____":
            raise Exception("Error: Gmm section doesn't match GMM_____ kind")
        h = f.read(4)     #readint 4bytes representing the hash (compatibility)
        l = f.read(4)     #readint 4bytes representing the name length
        #read string of l bytes
        name = f.read( int( struct.unpack('>i',   l )[0] )  ) 
        myfile['name'] = name
        g = f.read(1)     #read a char representing the gender
        gk = f.read(4)    #readint 4bytes representing the gaussian kind
        dim = f.read(4)   #readint 4bytes representing the dimension
        c = f.read(4)     #readint 4bytes representing the number of components
        gvect_header =  k + h + l + name + g + gk + dim + c
        myfile['header'] = gvect_header
        myfile['content'] = read_gaussian_container(f)
        return myfile

    f = open(input_file,'r')
    key = f.read(8)
    if key != 'GMMVECT_':  #gmm container
        raise Exception('Error: Not a GMMVECT_ file!')
    size = f.read(4)
    num = int(struct.unpack( '>i', size )[0]) #number of gmms
    main_header = key + struct.pack( '>i', 1 )
    FULL = 0
    files = []
    for n in range(num):
        files.append( read_gmm( f ) )

    f.close()

    file_basename = input_file[:-4]

    index = 0
    basedir,filename = os.path.split(file_basename)
    if output_dir != None:
        basedir = output_dir
        for f in files:
            newname = os.path.join(basedir, "%s%04d.gmm" % (filename, index))
        fd = open(newname, 'w')
        fd.write(main_header + f['header'] + f['content'])
        fd.close()
        index += 1
        

def rename_gmm(input_file,new_name_gmm_file):
    """Rename a gmm with a new speaker identifier(name) associated.""" 
    
    gmm = open(input_file,'r')
    new_gmm = open(input_file+'.new','w')

    kind = gmm.read(8)
    new_gmm.write(kind)

    num_gmm_string = gmm.read(4) 
    num_gmm = struct.unpack('>i', num_gmm_string )

    if num_gmm != (1,):
        print str(num_gmm) + " gmms"
        raise Exception('Loop needed for gmms')

    new_gmm.write(num_gmm_string)

    gmm_1 = gmm.read(8)
    new_gmm.write(gmm_1)

    nothing =  gmm.read(4) 
    new_gmm.write(nothing)

    str_len = struct.unpack('>i', gmm.read(4) )
    name = gmm.read(str_len[0])
    print new_name_gmm_file
    new_len = struct.pack('>i', len(new_name_gmm_file) )

    new_gmm.write(new_len)
    new_gmm.write(new_name_gmm_file)

    all_other = gmm.read()

    new_gmm.write(all_other)
    gmm.close()
    new_gmm.close()
    

def build_gmm(filebasename,name):
    """Build a gmm (Gaussian Mixture Model) file from a given wave with a 
    speaker identifier (name) associated."""

    diarization(filebasename)

    ident_seg(filebasename,name)

    extract_mfcc(filebasename)
    
    _train_init(filebasename)

    _train_map(filebasename)

#-------------------------------------
#   seg files and trim functions
#-------------------------------------
def seg2trim(segfile):
    """Take a wave and splits it in small waves in this directory structure
    <file base name>/<cluster>/<cluster>_<start time>.wav """
    basename = os.path.splitext(segfile)[0]
    s = open(segfile,'r')
    for line in s.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            clust = arr[7]
            st = float(arr[2]) / 100
            end = float(arr[3]) / 100
            try:
                mydir = os.path.join(basename, clust)
                os.makedirs( mydir )
            except os.error, e:
                if e.errno == 17:
                    pass
                else:
                    raise os.error
            wave_path = os.path.join(basename, clust, 
                                     "%s_%07d.%07d.wav" % (clust, int(st), 
                                                           int(end)))
            commandline = "sox %s.wav %s trim  %s %s" % (basename, wave_path, 
                                                         st, end)
            start_subprocess(commandline)
            ensure_file_exists( wave_path )
    s.close()

def seg2srt(segfile):
    """Take a seg file and convert it in a subtitle file (srt)."""
    def readtime(aline):
        return int(aline[2])

    basename = os.path.splitext(segfile)[0]
    s = open(segfile,'r')
    lines = []
    for line in s.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            lines.append(arr)
    s.close()

    lines.sort(key=readtime, reverse=False)
    fileoutput = basename+".srt"
    srtfile = open(fileoutput,"w")
    row = 0
    for line in lines:
        row = row + 1
        st = float(line[2]) / 100
        en = st + float(line[3]) / 100
        srtfile.write(str(row) + "\n")
        srtfile.write(humanize_time(st) + " --> " + humanize_time(en) + "\n")
        srtfile.write(line[7] + "\n")
        srtfile.write("\n")

    srtfile.close()
    ensure_file_exists(basename + '.srt')

def extract_mfcc(filebasename):
    """Extract audio features from the wave file, in particular the 
    mel-frequency cepstrum using a sphinx tool."""
    commandline = "sphinx_fe -verbose no -mswav yes -i %s.wav -o %s.mfcc" %  ( filebasename, filebasename )
    start_subprocess(commandline)
    ensure_file_exists(filebasename + '.mfcc')

def ident_seg(filebasename, name):
    """Substitute cluster names with speaker names ang generate a
    "<filebasename>.ident.seg" file."""
    ident_seg_rename(filebasename, name, filebasename + '.ident')
 
def ident_seg_rename(filebasename, name, outputname):
    """Take a seg file and substitute the clusters with a given name or 
    identifier."""
    f = open(filebasename + '.seg', 'r')
    clusters=[]
    lines = f.readlines()
    for line in lines:
        for k in line.split():
            if k.startswith('cluster:'):
                c = k.split(':')[1]
                clusters.append(c)
    f.close()
    output = open(outputname + '.seg', 'w')
    clusters.reverse()
    for line in lines:
        for c in clusters:
            line = line.replace(c,name)
        output.write(line)
    output.close()
    ensure_file_exists(outputname + '.seg')

def manage_ident(filebasename, gmm, clusters):
    """Take all the files created by the call of mfcc_vs_gmm() on the whole 
    speakers db and put all the results in a bidimensional dictionary."""
    f = open("%s.ident.%s.seg" % (filebasename,gmm ) ,"r")
    for l in f:
        if l.startswith(";;"):
            cluster, speaker = l.split()[ 1 ].split(':')[ 1 ].split('_')
            i = l.index('score:' + speaker) + len('score:' + speaker + " = ")
            ii = l.index(']', i) -1
            value = l[i:ii]
            if not clusters.has_key(cluster):
                clusters[ cluster ] = Cluster(cluster, 'U', '0', '')
            clusters[ cluster ].add_speaker( speaker, value )
            """
            if clusters[ cluster ].has_key( speaker ) == False:
                clusters[ cluster ][ speaker ] = float(value)
            else:
                if clusters[ cluster ][ speaker ] < float(value):
                    _clusters[ cluster ][ speaker ] = float(value)
            """
    f.close()
    if not keep_intermediate_files:
        os.remove("%s.ident.%s.seg" % (filebasename, gmm ) )

def extract_clusters(filename, clusters):
    """Read _clusters from segmentation file."""
    f = open(filename, "r")
    last_cluster = None
    for l in f:
        if l.startswith(";;"):
            speaker_id = l.split()[1].split(':')[1]
            clusters[ speaker_id ] = Cluster(name=speaker_id, gender='U', 
                                             frames=0, 
                                             dirname=os.path.splitext(filename)[0])
            last_cluster = clusters[ speaker_id ]
            last_cluster._seg_header = l
        else:
            line = l.split()
            last_cluster._segments.append(Segment(line))
            last_cluster._frames += int(line[3])
            last_cluster.gender = line[4]
            last_cluster._e = line[5]
    f.close()

def srt2subnames(filebasename, key_value):
    """Substitute cluster names with real names in subtitles."""

    def replace_words(text, word_dic):
        """
        take a text and replace words that match a key in a dictionary with
        the associated value, return the changed text
        """
        rc = re.compile('|'.join(map(re.escape, word_dic)))

        def translate(match):
            return word_dic[match.group(0)]+'\n'

        return rc.sub(translate, text)

    file_original_subtitle = open(filebasename + ".srt")
    original_subtitle = file_original_subtitle.read()
    file_original_subtitle.close()
    key_value = dict(map(lambda (key, value): (str(key) + "\n", value), 
                         key_value.items()))
    text = replace_words(original_subtitle, key_value)
    out_file = filebasename + ".ident.srt"
    # create a output file
    fout = open(out_file, "w")
    fout.write(text)
    fout.close()
    ensure_file_exists(out_file)

def file2trim(filename):
    """Take a video or audio file and converts it into smaller waves according
    to the diarization process."""
    if not quiet_mode: 
        print "*** converting video to wav ***"
    file2wav(filename)
    file_basename = os.path.splitext(filename)[0]
    if not quiet_mode: 
        print "*** diarization ***"
    diarization(file_basename)
    if not quiet_mode: 
        print "*** trim ***"
    seg2trim(file_basename+'.seg')

#--------------------------------------------
#   diarization and voice matching functions
#--------------------------------------------
def _silence_segmentation(filebasename): 
    start_subprocess( 'java -Xmx2024m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MSegInit --fInputMask=%s.mfcc --fInputDesc=audio16kHz2sphinx,1:1:0:0:0:0,13,0:0:0 --sInputMask= --sOutputMask=%s.s.seg ' +  filebasename )
    ensure_file_exists(filebasename+'.s.seg')
    
def _gender_detection(filebasename):
    start_subprocess( 'java -Xmx2024m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MDecode  --fInputMask=%s.wav --fInputDesc=audio2sphinx,1:3:2:0:0:0,13,0:0:0 --sInputMask=%s.s.seg --sOutputMask=%s.g.seg --dPenality=10,10,50 --tInputMask=' + sms_gmms + ' ' + filebasename )
    ensure_file_exists(filebasename+'.g.seg')
    cmd = 'java -Xmx2024m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MScore --help  --sGender --sByCluster --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:0:0 --fInputMask=%s.mfcc --sInputMask=%s.g.seg --sOutputMask=%s.seg --tInputMask=' + gender_gmms + ' ' + filebasename
    start_subprocess( cmd )
    ensure_file_exists(filebasename+'.seg')

def diarization(filebasename):
    """Take a wave file in the correct format and build a segmentation file. 
    The seg file shows how much speakers are in the audio and when they talk.
    """
    start_subprocess( 'java -Xmx2024m -jar '+lium_jar+' --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering ' +  filebasename )
    ensure_file_exists(filebasename+'.seg')

def _train_init(filebasename):
    """Train the initial speaker gmm model."""
    commandline = 'java -Xmx256m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainInit --sInputMask=%s.ident.seg --fInputMask=%s.wav --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4 --emInitMethod=copy --tInputMask=' + ubm_path + ' --tOutputMask=%s.init.gmm ' + file_basename
    start_subprocess(commandline)
    ensure_file_exists(filebasename+'.init.gmm')

def _train_map(filebasename):
    """Train the speaker model using a MAP adaptation method."""
    commandline = 'java -Xmx256m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainMAP --sInputMask=%s.ident.seg --fInputMask=%s.mfcc --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4 --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm ' + file_basename 
    start_subprocess(commandline)
    ensure_file_exists(filebasename+'.gmm')

def mfcc_vs_gmm(filebasename, gmm, gender, custom_db_dir=None):
    """Match a mfcc file and a given gmm model file."""
    database = db_dir
    if custom_db_dir != None:
        database = custom_db_dir
    gmm_name = os.path.split(gmm)[1]
    commandline = 'java -Xmx256M -cp ' + lium_jar + ' fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg --fInputMask=%s.mfcc --sOutputMask=%s.ident.' + gender + '.' + gmm_name + '.seg --sOutputFormat=seg,UTF8  --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:0:300:4 --tInputMask=' + database + '/' + gender + '/' + gmm + ' --sTop=8,' + ubm_path + '  --sSetLabel=add --sByCluster ' + filebasename 
    start_subprocess(commandline)
    ensure_file_exists(filebasename + '.ident.' + gender + '.' + gmm_name + '.seg')
    
#def threshold_tuning():
#    """ Get a score to tune up the threshold to define when a speaker is unknown"""
#    filebasename = os.path.join(test_path,'mr_arkadin')
#    gmm = "mrarkadin.gmm"
#    gender = 'M'
#    ensure_file_exists(filebasename+'.wav')
#    ensure_file_exists( os.path.join(test_path,gender,gmm ) )
#    file2trim(filebasename+'.wav')
#    extract_mfcc(filebasename)
#    mfcc_vs_gmm(filebasename, gmm, gender,custom_db_dir=test_path)
#    clusters = {}
#    extract_clusters(filebasename+'.seg',clusters)
#    manage_ident(filebasename,gender+'.'+gmm,clusters)
#    return clusters['S0'].speakers['mrarkadin']

def _interactive_training(filebasename, cluster, speaker):
    """A user interactive way to set the name to an unrecognized voice of a 
    given cluster."""
    info = None
    p = None
    if speaker == "unknown":
        info = """The system has not identified this speaker!"""
    else:
        info = "The system has identified this speaker as '"+speaker+"'!"

    print info

    while True:
        try:
            char = raw_input("\n 1) Listen\n 2) Set name\n Press enter to skip\n> ")
        except EOFError:
            print ''
            continue
        print ''
        if p != None and p.poll() == None:
            p.kill()
        if char == "1":
            videocluster = str(filebasename+"/"+cluster)
            listwaves = os.listdir(videocluster)
            listw = [os.path.join(videocluster, f) for f in listwaves]
            w = " ".join(listw)
            commandline = "play "+str(w)
            print "  Listening %s..." % cluster
            args = shlex.split(commandline)
            p = subprocess.Popen(args, stdin=output_redirect, stdout=output_redirect, 
                                 stderr=output_redirect)
            time.sleep(1)
            continue
        if char == "2":
            m = False
            while not m:
                name = raw_input("Type speaker name or leave blank for unknown speaker: ")
                while True:
                    if len(name) == 0:
                        name = "unknown"
                    if not name.isalnum() :
                        print 'No blanks, dashes or special characters are allowed! Retry'   
#                        m = True        
                        break
                    ok = raw_input("Save as '"+name+"'? [Y/n/m] ")
                    if ok in ('y', 'ye', 'yes',''):
                        return name
                    if ok in ('n', 'no', 'nop', 'nope'):
                        break
                    if ok in ('m',"menu"):
                        m = True
                        break
                if not m: 
                    print "Yes, no or menu, please!"  
            continue
        if char == "":
            return speaker
        print "Type 1, 2 or enter to skip, please"

#----------------------------------
# argument parsing facilities
#----------------------------------

def _multiargs_callback(option, opt_str, value, parser):
    """ Create an array from multiple args"""
    if len(parser.rargs) == 0:
        parser.error("incorrect number of arguments")
    args=[]
    for arg in parser.rargs:
        if arg[0] != "-":
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)

#------------------------------------------------------------
#  the actual main - argument parsing and functions calls
#------------------------------------------------------------
if __name__ == '__main__':
    usage = """%prog ARGS

examples:
    speaker identification
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -i INPUT_FILE
    
        user interactive mode
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -i INPUT_FILE -u    

    speaker model creation
        %prog [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g INPUT_FILE
        %prog [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g WAVE WAVE ... WAVE  MERGED_WAVES """

    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="verbose mode")
    parser.add_option("-q", "--quiet", dest="quiet_mode", action="store_true", default=False, help="suppress prints")
    parser.add_option("-k", "--keep-intermediatefiles", dest="keep_intermediate_files", action="store_true", help="keep all the intermediate files")
    parser.add_option("-i", "--identify",  dest="file_input", metavar="FILE", help="identify speakers in video or audio file")
    parser.add_option("-g", "--gmm", action="callback", callback=_multiargs_callback, dest="waves_for_gmm", help="build speaker model ")
    parser.add_option("-s", "--speaker", dest="speakerid", help="speaker identifier for model building")
    parser.add_option("-d", "--db",type="string", dest="dir_gmm", metavar="PATH",help="set the speakers models db path (default: %s)" % db_dir )
    parser.add_option("-j", "--jar",type="string", dest="jar", metavar="PATH",help="set the LIUM_SpkDiarization jar path (default: %s)" % lium_jar )
    parser.add_option("-b", "--ubm",type="string", dest="ubm", metavar="PATH",help="set the gmm UBM model path (default: %s)" % ubm_path)
    parser.add_option("-u", "--user-interactive", dest="interactive", action="store_true", help="User interactive training")
    parser.add_option("-f", "--output-format", dest="output_format",action="store", type="string", help="output file format [ srt | json | xmp ] (default srt)")

    (options, args) = parser.parse_args()

    if options.keep_intermediate_files:
        keep_intermediate_files = options.keep_intermediate_files
    if options.quiet_mode:
        quiet_mode = options.quiet_mode
    if options.dir_gmm:
        db_dir = options.dir_gmm
    if options.output_format:
        if options.output_format not in ('srt', 'json', 'xmp'):
            print 'output format (%s) wrong or not available' % options.output_format
            parser.print_help()
            exit(0)
        output_format = options.output_format
    if options.jar:
        lium_jar = options.jar
    if options.ubm:
        ubm_path = options.ubm      

    check_deps()
           
    if options.file_input:
        
        #create db istance
        default_db = GMMVoiceDB(path=db_dir)
        
        #create voiceid instance
        cmanager = Voiceid(db=default_db, filename=options.file_input)
        
        #extract the speakers
        cmanager.extract_speakers(interactive=options.interactive, 
                                  quiet=quiet_mode, thrd_n=cpu_count() * 5)
        
        #write the output according to the given output format
        cmanager.write_output( output_format )
        
        if not keep_intermediate_files:
            os.remove(cmanager.get_file_basename() + '.seg')            
            os.remove(cmanager.get_file_basename() + '.mfcc')
            w = cmanager.get_file_basename() + '.wav'
            if cmanager.get_filename() != w:
                os.remove(w)
            shutil.rmtree(cmanager.get_file_basename())
        exit(0)
        
    if options.waves_for_gmm and options.speakerid:
        file_basename = None
        waves = options.waves_for_gmm
        speaker = options.speakerid
        if not speaker.isalnum():
            print 'error: SPEAKER_ID must be alphanumeric'
            exit(1)
        w = None
        if len(waves)>1:
            merge_waves(waves[:-1], waves[-1])
            w = waves[-1]
        else:
            w = waves[0]
        basename, extension = os.path.splitext(w)
        file_basename = basename
        file2wav(w)
        build_gmm(file_basename, speaker)
        exit(0)

    parser.print_help()
