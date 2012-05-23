#############################################################################
#
# VoiceID, Copyright (C) 2011-2012, Sardegna Ricerche.
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
"""Module containing classes relatives to the speaker recognition task."""

import os
import shlex
import shutil
import subprocess
import time
from __init__ import KEEP_INTERMEDIATE_FILES, output_redirect
from threading import Thread
from utils import ensure_file_exists, humanize_time
from fm import merge_waves, extract_mfcc, file2wav, _silence_segmentation, \
    _gender_detection, diarization, seg2trim, wave_duration, seg2srt, srt2subnames


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
        
    def __cmp__(self, other):
        if self._start < other._start:
            return -1
        if self._start > other._start:
            return 1
        return 0
    
    def rename(self, identifier):
        """Change the identifier of the segment.
        
        :type identifier: string
        :param identifier: the identifier of the speaker in the segment"""
        self._line[7] = self._speaker = identifier

    def get_basename(self):
        """Get the basename of the original file which belong the segment."""
        return self._basename

    def get_start(self):
        """Get the start frame index of the segment."""
        return self._start
    
    def get_end(self):
        """Get the end frame index of the segment."""
        return self._start + self._duration 
    
    def get_duration(self):
        """Get the duration of the segment in frames."""
        return self._duration

    def get_gender(self):
        """Get the gender of the segment."""
        return self._gender

    def get_environment(self):
        """Get the environment of the segment."""
        return self._environment

    def get_speaker(self):
        """Get the speaker identifier of the segment."""
        return self._speaker

    def get_line(self):
        """Get the line of the segment in the original seg file.""" 
        return self._line

class Cluster:
    """A Cluster object, representing a computed cluster for a single
    speaker, with gender, a number of frames and environment.

    :type identifier: string
    :param identifier: the cluster identifier
    
    :type gender: char F, M or U                   
    :param gender: the gender of the cluster
    
    :type frames: integer
    :param frames: total frames of the cluster
    
    :type dirname: string
    :param dirname: the directory where is the cluster wave file"""

    
    def __init__(self, identifier, gender, frames, dirname, label=None):
        """
        :type identifier: string
        :param identifier: the cluster identifier
        
        :type gender: char F, M or U                   
        :param gender: the gender of the cluster
        
        :type frames: integer
        :param frames: total frames of the cluster
        
        :type dirname: string
        :param dirname: the directory where is the cluster wave file"""
        
        self.gender = gender
        self._frames = frames
        self._e = None #environment (studio, telephone, unknown)
        self._label = label
        self._speaker = identifier
        self._segments = []
        self._seg_header = ";; cluster:%s [ score:FS = 0.0 ] [ score:FT = 0.0 ] [ score:MS = 0.0 ] [ score:MT = 0.0 ]\n" % identifier
        self.speakers = {}
        self.up_to_date = True
        self.wave = dirname + '.wav'
        self.mfcc = dirname + '.mfcc'
        self.dirname = dirname
        
    def __str__(self):
        return "%s (%s)" % (self._label, self._speaker)

    def add_speaker(self, identifier, score):
        """Add a speaker with a computed score for the cluster, if a better 
        score is already present the new score will be ignored.
        
        :type identifier: string
        :param identifier: the speaker identifier
        
        :type score: float
        :param score: score computed between the cluster wave and speaker model
        """
        v = float(score)
        if self.speakers.has_key( identifier ) == False:
            self.speakers[ identifier ] = v
        else:
            if self.speakers[ identifier ] < v:
                self.speakers[ identifier ] = v

    def get_speaker(self):
        """Set the right speaker for the cluster if not set and returns
         its name."""
        if self._speaker == None:
            self._speaker = self.get_best_speaker()
        return self._speaker
    
    def set_speaker(self, identifier):
        """Set the cluster speaker identifier 'by hand'.
        
        :type identifier: string
        :param identifier: the speaker name or identifier 
        """
        self.up_to_date = False
        self._speaker = identifier

    def get_mean(self):
        """Get the mean of all the scores of all the tested speakers for
         the cluster."""
        try:
            return sum(self.speakers.values()) / len(self.speakers)
        except:
            return 0.0
            
    def get_name(self):
        """Get the cluster name assigned by the diarization process."""
        return self._label

    def get_best_speaker(self):
        """Get the best speaker for the cluster according to the scores.
         If the speaker's score is lower than a fixed threshold or is too
         close to the second best matching voice, 
         then it is set as "unknown".
         
         :rtype: string
         :returns: the best speaker matching the cluster wav
         """
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
        if distance < .07:
            self._speaker = 'unknown'
        return self._speaker
    
    def get_best_five(self):
        """Get the best five speakers in the db for the cluster.
        
        :rtype: array of tuple
        :returns: an array of five most probable speakers represented by ordered tuples of the form (speaker, score) ordered by score.
        """
        return sorted(self.speakers.iteritems(), key=lambda (k,v): (v,k),
                      reverse=True)[:5]
    
    def get_gender(self):
        """Get the computed gender of the Cluster.
        
        :rtype: char
        :returns: the gender of the cluster
        """
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

    def _generate_a_seg_file(self, filename, first_col_name):
        """Generate a segmentation file for the given showname.

        :type filename: string
        :param filename: the name of the seg file
        
        :type first_col_name: string
        :param first_col_name: the name in the first column of the seg file,
               in fact the name and path of the corresponding wave file
        """
        f = open(filename, 'w')
        f.write(self._seg_header)
        line = self._segments[0].get_line()[:]
        line[0] = first_col_name
        line[2] = 0
        line[3] = self._frames - 1
        f.write("%s %s %s %s %s %s %s %s\n" % tuple(line) )
        f.close()
        
    def merge(self, other):
        """Merge the Cluster with another.
        
        :type other: Cluster
        :param other: the cluster to be merged with"""
        self._segments.extend(other._segments)
        self._segments.sort()

    def rename(self, label):
        """Rename the cluster and all the relative segments.
        
        :type label: string
        :param label: the new name of the cluster"""
        self._seg_header = self._seg_header.replace(self._label, label)
        self._label = label
        for s in self._segments:
            s.rename(label)
        
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
        except IOError:
            extract_mfcc(file_basename)
            
    def to_dict(self):
        """A dictionary representation of a Cluster."""
        speaker = self.get_speaker()
        segs = []
        for s in self._segments:
            t = s._line[2:]
            t[-1] = speaker
            t[0] = int(s.get_start())
            t[1] = int(s.get_end())
            t.append(self.get_name()) 
            segs.append(t)
        return segs
    
    def print_segments(self):
        """Print cluster timing."""
        for s in self._segments:
            print "%s to %s" % ( humanize_time( float(s.get_start()) / 100 ),
                                 humanize_time( float(s.get_end()) / 100 ) )
            
    def _get_seg_repr(self):
        result = str(self._seg_header)
        for s in self._segments:
            line = s.get_line()
            line[-1] = self._speaker
            result += "%s %s %s %s %s %s %s %s\n" % tuple(line)
        return result
            

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
    @staticmethod 
    def from_json_file(db, json_filename):
        """Build a Voiceid object from json file.
        
        :type json_filename: string
        :param json_filename: the file containing a json style python dictionary representing a Voiceid object instance
        """
        of = open(json_filename, 'r')
        jdict = eval(of.read())
        of.close()
        return Voiceid.from_dict(db, jdict)

    @staticmethod 
    def from_dict(db, json_dict):
        """Build a Voiceid object from json dictionary.
        
        :type json_dict: dictionary
        :param json_dict: the json style python dictionary representing a Voiceid object instance
        """
        v = Voiceid(db, json_dict['url'])
        dirname = os.path.splitext(json_dict['url'])[0]
        try:
            for e in json_dict['selections']:            
                c = v.get_cluster(e['speakerLabel'])
                if not c:
                    c = Cluster(e['speaker'], e['gender'], 0, dirname, e['speakerLabel'])
                s = Segment([dirname, 1, int(e['startTime'] * 100), 
                             int( 100 * (e['endTime'] - e['startTime']) ), 
                             e['gender'], 'U', 'U', e['speaker'] ])
                c._segments.append(s)
                v.add_update_cluster(e['speakerLabel'], c)
        except:
            raise Exception('ERROR: Failed to load the dictionary, maybe is in wrong format!')
        return v

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
        """Get the status of the computation.
            0:'file_loaded', 
            1:'file_converted', 
            2:'diarization_done', 
            3:'trim_done', 
            4:'mfcc extracted', 
            5:'speakers matched'
        """
        return self._status

    def get_working_status(self):
        """
        Get a string representation of the working status.
            0:'converting_file', 
            1:'diarization',
            2:'trimming', 
            3:'mfcc extraction',
            4:'voice matching', 
            5:'extraction finished'"""
        #TODO: fix some issue on restarting and so on about current status
        return self.working_map[ self.get_status() ]  
    
    def get_db(self):
        """Get the VoiceDB instance used."""
        return self._db
    
    #setters and getters
    def _get_interactive(self):
        return self._interactive

    def _set_interactive(self, value):
        self._interactive = value

    def get_clusters(self):
        """Get the clusters recognized in the processed file.
        """
        return self._clusters

    def _set_clusters(self, value):
        self._clusters = value

    def _get_time(self):
        return self._time

    def _set_time(self, value):
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
        
    def get_cluster(self, label):
        """Get a the cluster by a given label.
        
        :type label: string
        :param label: the cluster label (i.e. S0, S12, S44...)
        """
        try:
            return self._clusters[ label ]
        except:
            return None
    
    def add_update_cluster(self, label, cluster):
        """Add a cluster or update an existing cluster.

        :type label: string
        :param label: the cluster label (i.e. S0, S12, S44...)
        
        :type cluster: object
        :param cluster: a Cluster object
        """
        self._clusters[ label ] = cluster
        
    def remove_cluster(self, label):
        """Remove and delete a cluster. 

        :type label: string
        :param label: the cluster label (i.e. S0, S12, S44...)
        """
        del self._clusters[label]
        
    def get_time_slices(self):
        """Return the time slices with all the information about start time,
        duration, speaker name or "unknown", gender and sound quality
        (studio/phone)."""
        tot = []
        for c in self._clusters:
             
            tot.extend(self._clusters[c].to_dict()[:])
        #tot.sort()
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
        
    def generate_seg_file(self):
        """Generate a seg file according to the information acquired about the speech clustering"""
        result = ''
        for c in self._clusters:
            result += self._clusters[c]._get_seg_repr()
            
        f = open(self.get_file_basename() + '.seg', 'w')
        f.write(result)
        f.close()
        
    def diarization(self):
        """Run the diarization process. In case of single mode (single speaker 
        in the input file) just create the seg file with silence and gender 
        detection."""
        if self._single:
            self._to_MFCC()
            try:
                os.mkdir(self.get_file_basename())
            except OSError,e:
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
#                       then set the prevailing
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
        seg2trim(self._basename)
        
    def _extract_clusters(self):
        extract_clusters(self._basename+'.seg', self._clusters)
        
    def _match_clusters(self, interactive=False, quiet=False):
        basename = self.get_file_basename()
        #merging segments wave files for every cluster
        for cluster in self._clusters:
            self[cluster].merge_waves(basename)
            self[cluster].generate_seg_file(os.path.join(basename, 
                                                         cluster + ".seg"))
        """
        for cluster in self._clusters:            
            filebasename = os.path.join(basename, cluster)
            results = self.get_db().voice_lookup(filebasename + '.mfcc', 
                                                 self[cluster].gender)
            for r in results:
                self[cluster].add_speaker(r, results[r])
        """
        mfcc_files = {}
        for cluster in self._clusters:                        
            filebasename = os.path.join(basename, cluster) + '.mfcc'
            mfcc_files[ filebasename ] = self[cluster].gender

        res = self.get_db().voices_lookup(mfcc_files)
                       
        def mfcc_to_cluster(mfcc):
            return mfcc.split("/")[-1].split(".")[0]
        
        for rr in res:
            cluster = mfcc_to_cluster(rr)
            for r in res[rr].keys():
                self[cluster].add_speaker(r, res[rr][r])
            
        if not quiet: 
            print ""
        speakers = {}
        
        for c in self._clusters:
            if not quiet: 
                if interactive: 
                    print "**********************************"
                    print "speaker ", c
                    self[c].print_segments()
            speakers[c] = self[c].get_best_speaker()
            """
            if not interactive: 
                for speaker in self[c].speakers:
                    if not quiet: 
                        print "\t %s %s" % (speaker, self[c].speakers[speaker])
                if not quiet: 
                    print '\t ------------------------'
                    
            """
            
             
            if interactive == True:
                self._set_interactive( True )
                
                speakers[c] = best = _interactive_training(basename, 
                                                          c, speakers[c])
                self[c].set_speaker(best)
    
    def _rename_clusters(self):
        all_clusters = []
        temp_clusters = self._clusters.copy() 
        for c in temp_clusters:
            all_clusters.append( self._clusters.pop(c) )
        i = 0
        for c in all_clusters:
            label = 'S'+str(i)
            c.rename(label)
            self._clusters[label] = c
            i += 1
    
    def _merge_clusters(self, c1, c2):
        
        label = ''
        to_delete = ''
        if c1 < c2:
            label = c1
            to_delete = c2
        else:
            label = c2
            to_delete = c1
            
        to_keep = self.get_cluster(label)
        to_remove = self._clusters.pop(to_delete)
            
        to_keep.merge(to_remove)
        
    def automerge_clusters(self):
        """Check for Clusters representing the same speaker and merge them."""
        all_clusters = self.get_clusters().copy()
        
        if not self._single:
            changed = False
            for c1 in all_clusters:
                c_c1 = all_clusters[c1]
                for c2 in all_clusters:
                    c_c2 = all_clusters[c2]
                    if c1 != c2 and c_c1.get_speaker() != 'unknown' and c_c1.get_speaker() == c_c2.get_speaker() and self._clusters.has_key(c1) and self._clusters.has_key(c2):
                        changed = True 
                        self._merge_clusters(c1, c2)
            if changed:            
                self._rename_clusters()
                shutil.rmtree(self.get_file_basename())
                self.generate_seg_file()
                self._to_trim()                

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
        
        self._match_clusters(interactive, quiet)
        
        if not interactive:
            #merging
            self.automerge_clusters()
   
        sec = wave_duration( basename+'.wav' )
        total_time = time.time() - start_time
        self._set_time( total_time )
        self._status = 5
        if not quiet: print self.get_working_status()
        if interactive:
            print "Updating db"
            self.update_db(thrd_n)

        if not interactive:
            if not quiet: 
                for c in self._clusters:
                    print "**********************************"
                    print "speaker ", c
                    for speaker in self[c].speakers:
                        print "\t %s %s" % (speaker, self[c].speakers[speaker])
                    print '\t ------------------------'
                    distance = self[c].get_distance()
                        
                    try:
                        mean = self[c].get_mean()
                        m_distance = self[c].get_m_distance()
                    except:
                        mean = 0
                        m_distance = 0
            
                    print """\t best speaker: %s (distance from 2nd %f - mean %f - distance from mean %f ) """ % (self[c],
                                                                                                              distance,
                                                                                                                  mean, m_distance)         
    
                
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
            
    def _match_voice_wrapper(self, cluster, mfcc_name, db_entry, gender):
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
        def _get_available_wav_basename(label, basedir):
            cont = 0
            label = os.path.join(basedir, label)
            wav_name = label + ".wav"
            if os.path.exists(wav_name):
                while True: #search an inexistent name for new gmm
                    cont = cont +1
                    wav_name = label + "" + str(cont) + ".wav"
                    if not os.path.exists(wav_name):
                        break
            return label + str(cont)
        
        
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
            if not KEEP_INTERMEDIATE_FILES:
                try:
                    os.remove("%s.seg" % wave_b )
                    os.remove("%s.mfcc" % wave_b )
#                    os.remove("%s.ident.seg" % wave_b )
                    os.remove("%s.init.gmm" % wave_b )
                    os.remove("%s.wav" % wave_b )
                except:
                    pass
            #end _build_model_wrapper
        
        #merge all clusters relatives to the same speaker
        self.automerge_clusters()
        
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
                                     "startTime" : float(s[0]) / 100.0,
                                     "endTime" : float(s[1]) / 100.0,
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
            self.generate_seg_file()
            seg2srt(self.get_file_basename() + '.seg')
#            srt2subnames(self.get_file_basename(), self.get_speakers_map())
#            shutil.move(self.get_file_basename() + '.ident.srt', 
#                        self.get_file_basename() + '.srt')
            
        if mode == 'json':
            self.write_json()
        
        if mode == 'xmp':
            file_xmp = open(self.get_file_basename() + '.xmp', 'w')
            file_xmp.write(str(self.to_XMP_string()))
            file_xmp.close()




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
                clusters[ cluster ] = Cluster(cluster, 'U', '0', '',cluster)
            clusters[ cluster ].add_speaker( speaker, value )
            """
            if clusters[ cluster ].has_key( speaker ) == False:
                clusters[ cluster ][ speaker ] = float(value)
            else:
                if clusters[ cluster ][ speaker ] < float(value):
                    _clusters[ cluster ][ speaker ] = float(value)
            """
    f.close()
    if not KEEP_INTERMEDIATE_FILES:
        os.remove("%s.ident.%s.seg" % (filebasename, gmm ) )

def extract_clusters(segfilename, clusters):
    """Read _clusters from segmentation file."""
    f = open(segfilename, "r")
    last_cluster = None
    for l in f:
        if l.startswith(";;"):
            speaker_id = l.split()[1].split(':')[1]
            clusters[ speaker_id ] = Cluster(identifier='unknown', gender='U', 
                                             frames=0, 
                                             dirname=os.path.splitext(segfilename)[0],label=speaker_id)
            last_cluster = clusters[ speaker_id ]
            last_cluster._seg_header = l
        else:
            line = l.split()
            last_cluster._segments.append(Segment(line))
            last_cluster._frames += int(line[3])
            last_cluster.gender = line[4]
            last_cluster._e = line[5]
    f.close()

def _interactive_training(filebasename, cluster, identifier):
    """A user interactive way to set the name to an unrecognized voice of a 
    given cluster."""
    info = None
    p = None
    if identifier == "unknown":
        info = """The system has not identified this speaker!"""
    else:
        info = "The system has identified this speaker as '"+identifier+"'!"

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
            return identifier
        print "Type 1, 2 or enter to skip, please"
