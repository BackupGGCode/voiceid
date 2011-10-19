#!/usr/bin/env python
#########################################################################
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
#########################################################################

from optparse import OptionParser
from multiprocessing import cpu_count
import os
import shlex, subprocess
import time
import re
import shutil
import struct
import threading

#-------------------------------------
#   classes
#-------------------------------------
class VoiceDB:
    """ A class that represent a voice db"""
    def __init__(self, path):
        self._path = path
        self._genders = ['M','F','U']
        self._read_db()

    def get_path(self):
        """ Get the base path of the voice db"""
        return self._path
    
    def _read_db(self):
        pass
    
    def add_model(self, basepath, speaker_name, gender):
        pass
    
    def remove_model(self, mfcc_file, speaker, gender, value):
        pass 
    
    def match_voice(self, mfcc_file, speakername, gender):
        pass
    
class GMMVoiceDB(VoiceDB):
    """ A Gaussian Mixture Model voice database """    
    def _read_db(self):
        """ Read for any changes the db voice models files """
        self._speakermodels = {}
        for g in self._genders:
            self._speakermodels[ g ] = [ f for f in os.listdir(os.path.join(self._path, g )) if f.endswith('.gmm') ]
    
    def add_model(self, basepath, speaker_name, gender):
        """ Add a gmm model to db """
        ident_seg(basepath, speaker_name)
        train_init(basepath)
        extract_mfcc(basepath)
        train_map(basepath)
        
        gmm_path = basepath+'.gmm'
        original_gmm =  os.path.join(self.get_path(), gender, speaker_name+'.gmm')
        try:
            ensure_file_exists(original_gmm)
            merge_gmms([original_gmm,gmm_path],original_gmm)
            self._read_db()
            return True
        except Exception,e:
            if str(e) == "File %s doesn't exist or not correctly created"  % original_gmm:
                shutil.copy(gmm_path, original_gmm)
                self._read_db()
                return True
        return False
    
    def remove_model(self, mfcc_file, speaker, gender, value):
        """ Remove a voice model from the db """
        old_s = speaker
        
        folder_db_dir = os.path.join(self.get_path(),gender)
        
        if os.path.exists(os.path.join(folder_db_dir,old_s+".gmm")):
            folder_tmp = os.path.join(folder_db_dir,old_s+"_tmp_gmms")
            if not os.path.exists(folder_tmp):
                os.mkdir(folder_tmp)
                
            split_gmm(os.path.join(folder_db_dir,old_s+".gmm"),folder_tmp)
            listgmms = os.listdir(folder_tmp)
            filebasename = os.path.splitext(mfcc_file)[0]
            value_old_s = value
            
            if len(listgmms) != 1:
                for gmm in listgmms:
                    mfcc_vs_gmm(filebasename, os.path.join(old_s+"_tmp_gmms",gmm), gender)
                    f = open("%s.ident.%s.%s.seg" % (filebasename, gender, gmm) , "r")
                    for l in f:
                        if l.startswith(";;"):
                            speaker = l.split()[ 1 ].split(':')[ 1 ].split('_')[1]
                            i = l.index('score:' + speaker) + len('score:' + speaker + " = ")
                            ii = l.index(']', i) - 1
                            value_tmp = l[i:ii]
                            if float(value_tmp) == value_old_s:
                                os.remove(os.path.join(folder_tmp, gmm))
                merge_gmms(listgmms, os.path.join(folder_db_dir,old_s+".gmm"))
                
            else:
                os.remove(os.path.join(folder_db_dir,old_s+".gmm")) #remove the 
            shutil.rmtree(folder_tmp)
            self._read_db()
             
    def match_voice(self, mfcc_file, speakername, gender):
        """ Match the voice (mfcc file) versus the gmm model of 'speakername' in db """
        mfcc_basename = os.path.splitext(mfcc_file)[0]
                
        mfcc_vs_gmm( mfcc_basename , speakername+'.gmm', gender, self.get_path() )
        cls = {}
        manage_ident( mfcc_basename, gender+'.'+speakername+'.gmm', cls )
        s = {}
        for c in cls:
            s.update( cls[ c ].speakers )
        return s

class Segment:
    """ A Segment taken from seg file, representing the smallest recognized voice time slice """
    
    def __init__(self, line):
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
        return self._start+self._duration 
    
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
    """ A Cluster object, representing a computed cluster for a single speaker, with gender, a number of frames and environment """
    
    def __init__(self, name, gender, frames, dirname ):
        """ Constructor of a Cluster object"""
        self.gender = gender
        self._frames = frames
        self._e = None #environment (studio, telephone, unknown)
        self._name = name
        self._speaker = None
        self._segments = []
        self._seg_header = None
        self.speakers = {}
        self.wave = None
        self.mfcc = None
        self.dirname = dirname

    def add_speaker(self, name, value):
        """ Add a speaker with a computed score for the cluster, if a better value is already present the new value will be ignored."""
        v = float(value)
        if self.speakers.has_key( name ) == False:
            self.speakers[ name ] = v
        else:
            if self.speakers[ name ] < v:
                self.speakers[ name ] = v

    def get_speaker(self):
        """ Set the right speaker for the cluster if not set and returns its name """
        if self._speaker == None:
            self._speaker = self.get_best_speaker()
        return self._speaker
    
    def set_speaker(self,speaker):
        """ Set the cluster speaker 'by hand' """
        self._speaker = speaker

    def get_mean(self):
        """ Get the mean of all the scores of all the tested speakers for the cluster"""
        return sum(self.speakers.values()) / len(self.speakers) 

    def get_name(self):
        """ Get the cluster name assigned by the diarization process"""
        return self._name

    def get_best_speaker(self):
        """ Get the best speaker for the cluster according to the scores. If the speaker's score is lower than a fixed threshold or is too close to the second best matching voice, then it is set as "unknown" """
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

    def get_distance(self):
        """ Get the distance between the best speaker score and the closest speaker score"""
        values = self.speakers.values()
        values.sort(reverse=True)
        try:
            return abs(values[1]) - abs(values[0])
        except:
            return 1000.0

    def get_m_distance(self):
        """ Get the distance between the best speaker score and the mean of all the speakers' scores""" 
        value = max(self.speakers.values())
        return abs( abs( value ) - abs( self.get_mean() ) )

    def generate_seg_file(self, filename):
        """ Generate a segmentation file for the cluster"""
        self._generate_a_seg_file(filename,self.wave[:-4])

    def _generate_a_seg_file(self, filename, name):
        """ Generate a segmentation file for the given showname"""
        f = open(filename,'w')
        f.write(self._seg_header)
        line = self._segments[0].get_line()
        line[0]=name
        line[2]=0
        line[3]=self._frames-1
        f.write("%s %s %s %s %s %s %s %s\n" % tuple(line) )
        f.close()
        
    def merge_waves(self, dirname):
        """  Take all the wave of a cluster and build a single wave"""        
        name = self.get_name() 
        videocluster =  os.path.join( dirname, name )
        
        listwaves = os.listdir( videocluster )
        
        listw = [ os.path.join( videocluster, f ) for f in listwaves ]
        
        file_basename = os.path.join( dirname, name )
        
        self.wave = os.path.join(dirname,name+".wav")
        
        merge_waves(listw,self.wave)      
        
        try:
            ensure_file_exists(file_basename+'.mfcc')
        except:
            extract_mfcc(file_basename)
            
    def to_dict(self):
        """ A dictionary representation of a Cluster """
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
        """ Print cluster timing """
        for s in self._segments:
            print "%s to %s" % ( humanize_time( float(s.get_start())/100 ), humanize_time( float(s.get_end())/100 ) )

class Voiceid:
    """ The main object that represents the file audio/video to manage. """

    @staticmethod
    def from_dict(db,json_dict):
        """ Build a Voiceid object from json dictionary """
        v = Voiceid(db, json_dict['url'])
        dirname = os.path.splitext(json_dict['url'])
        
        for e in json_dict['selections']:            
            c = v.get_cluster(e['speakerLabel'])
            if not c:
                c = Cluster(e['speaker'], e['gender'], 0, dirname)
            s = Segment([dirname,1,int(e['startTime']*100),int( 100*(e['endTime']-e['startTime']) ), e['gender'], 'U', 'U', e['speaker'] ])
            c._segments.append(s)
            v.add_update_cluster(e['speakerLabel'], c)
        return v

    def __init__(self, db, filename ):
        """ Initializations"""
        self.status_map = {0:'file_loaded',1:'file_converted',2:'diarization_done',3:'trim_done',4:'mfcc extracted',5:'speakers matched'} 
        self.working_map = {0:'converting_file',1:'diarization',2:'trimming',3:'mfcc extraction',4:'voice matching',5:'extraction finished'}
        self._clusters = {}
        self._ext = ''       
        self._time = 0
        self._interactive = False 
        self._db = db
        ensure_file_exists(filename)
        self.set_filename(filename)
        self._status = 0  
            
    def __getitem__(self,key):
        return self._clusters.__getitem__(key)
    
    def __iter__(self):
        """ Just iterate over the cluster's dictionary"""
        return self._clusters.__iter__()
    
    def get_status(self):
        return self._status

    def get_working_status(self):
        return self.working_map[ self.get_status() ]  #TODO: fix some issue on restarting and so on about current status
    
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
    
    def set_filename(self,filename):
        """ Set the filename of the current working file"""
        
        new_file_input = filename
        new_file_input=new_file_input.replace("'",'_').replace('-','_').replace(' ','_')
        try:
            shutil.copy(filename,new_file_input)
        except shutil.Error, e:
            if  str(e) == "`%s` and `%s` are the same file" % (filename,new_file_input):
                pass
            else:
                raise e
        ensure_file_exists(new_file_input)
        
        self._filename = new_file_input
        self._basename, self._ext = os.path.splitext(self._filename)
        
    def get_filename(self):
        """ Get the name of the current working file"""
        return self._filename
        
    def get_file_basename(self):
        """ Get the basename of the current working file"""
        return self._basename[:]
    
    def get_file_extension(self):
        """ Get the extension of the current working file"""
        return self._ext[:]
        
    def get_cluster(self,identifier):
        """ Get a the cluster by a given identifier"""
        try:
            return self._clusters[ identifier ]
        except:
            return None
    
    def add_update_cluster(self, identifier, cluster):
        """ Add a cluster or update an existing cluster"""
        self._clusters[ identifier ] = cluster
        
    def remove_cluster(self, identifier):
        """ Remove the cluster from the cluster manager"""
        del self._clusters[identifier]
        
    def get_time_slices(self):
        """ Return the time slices with all the information about start time, duration, speaker name or "unknown", gender and sound quality (studio/phone)"""
        tot = []
        for c in self._clusters:
            tot.extend(self._clusters[c].to_dict()[:])
        tot.sort()
        return tot

    def get_speakers_map(self):
        """ A dictionary map between speaker label and speaker name"""
        speakers = {}
        for c in self:
            speakers[c] = self[c].get_best_speaker()
        return speakers
    
    def to_wav(self):
        video2wav(self.get_filename())
        
    def diarization(self):
        diarization(self._basename)
        
    def to_MFCC(self):
        extract_mfcc(self._basename)
    
    def to_trim(self):
        seg2trim(self._basename+'.seg')
        
    def extract_clusters(self):
        extract_clusters(self._basename+'.seg', self._clusters)

    def extract_speakers(self, interactive=False, quiet=False, thrd_n=1):
        """ Identifie the speakers in the audio wav according to a speakers database. 
        If a speaker doesn't match any speaker in the database then sets it as unknown. 
        In interactive mode it asks the user to set speakers' names."""
        
        if thrd_n < 1: thrd_n = 1
        
        self._status = 0
        start_time = time.time()
        if not quiet: print self.get_working_status()
        self.to_wav()
        
        self._status = 1    
        
        if not quiet: print self.get_working_status()
        
        self.diarization()
        
        self._status = 2   
        if not quiet: print self.get_working_status()        
        self.to_trim()
        
        self._status = 3  
        if not quiet: print self.get_working_status()
        diarization_time = time.time() - start_time

        self.to_MFCC()
        self._status = 4 
        basename = self.get_file_basename()

        if not quiet: print self.get_working_status()
        self.extract_clusters()
        
        #merging segments wave files for every cluster
        for cluster in self._clusters:
            self[cluster].merge_waves(basename)
            self[cluster].generate_seg_file( os.path.join( basename, cluster+".seg" ) )
    
        t = {}
        files_in_db = self.get_db()._speakermodels  #TODO: avoid to look directly at the db entries 

        def match_voice_wrapper(cluster, mfcc_name, db_entry, gender ):
            """ A wrapper to match the voices each in a different Thread """
            results = self.get_db().match_voice( mfcc_name, db_entry, gender)
            for r in results:
                self[cluster].add_speaker( r, results[r] )
                
        def alive_threads():
            """ Check how much threads are running and alive """ 
            num = 0
            for thr in t:
                if t[thr].is_alive():
                    num += 1
            return num
        
       
        for cluster in self._clusters:            
            files = files_in_db[ self[cluster].gender ]
            filebasename = os.path.join(basename,cluster)
            for f in files:                
                if  alive_threads()  < thrd_n :
                    t[f+cluster] = threading.Thread( target=match_voice_wrapper, args=( cluster ,  filebasename+'.mfcc', os.path.splitext(f)[0], self[cluster].gender ) )
                    t[f+cluster].start()
                else:
                    while alive_threads() > thrd_n:
                        time.sleep(1)
                    t[f+cluster] = threading.Thread( target=match_voice_wrapper, args=( cluster,  filebasename+'.mfcc', os.path.splitext(f)[0], self[cluster].gender ) )
                    t[f+cluster].start()                    
                    
        for thr in t:
            if t[thr].is_alive():
                t[thr].join()
                
        if not quiet: print ""
        speakers = {}
        for c in self._clusters:
            if not quiet: 
                print "**********************************"
                print "speaker ", c
                if interactive: self[c].print_segments()
            speakers[c] = self[c].get_best_speaker()
            if not interactive: 
                for speaker in self[c].speakers:
                    if not quiet: print "\t %s %s" % (speaker , self[c].speakers[ speaker ])
                if not quiet: print '\t ------------------------'
            try:
                distance = self[c].get_distance()
            except:
                distance = 1000.0
            try:
                mean = self[c].get_mean()
                m_distance = self[c].get_m_distance()
            except:
                mean = 0
                m_distance = 0
    
            threads = {}
            
            if interactive == True:
                self.set_interactive( True )
                
                best = interactive_training(basename, c, speakers[c])
                
                old_s = speakers[c]
                speakers[c] = best
                self[c].set_speaker(best)
                
                if old_s != speakers[c] : # interactive training results don't match batch training results 
                    
#                    if old_s != "unknown" : # the wrong (batch calculated) name of the speaker is not 'unknown' 
#                        self.get_db().remove_model( os.path.join( basename, c) + '.mfcc', old_s, gender, self[c].value )  #remove the speaker model ---
                    
                    if speakers[c] != 'unknown': #the new speaker is not 'unknown'
                        
                        cont = 0
                        wav_name = speakers[c]+".wav"
                        if os.path.exists(wav_name):
                            while True: #search an inexistent name for new gmm
                                cont = cont +1
                                wav_name = speakers[c]+""+str(cont)+".wav"
                                if not os.path.exists(wav_name):
                                    break
                        basename_file = os.path.splitext(wav_name)[0]
                        
                        self[c].merge_waves(basename)
                        
                        shutil.move(self[c].wave, wav_name)
                        
                        if not quiet: print "name speaker %s " % speakers[c]
                        
                        def build_model_wrapper(wave_b, cluster, wave_dir, old_speaker):
                            """ A procedure to wrap the model building to run in a Thread """
                            try:
                                ensure_file_exists(wave_b+'.seg')
                            except:
                                self[cluster]._generate_a_seg_file( wave_b+'.seg', wave_b)                             
                         
                            ensure_file_exists(wave_b+'.wav')
                            new_speaker = self[cluster].get_speaker()
                            self.get_db().add_model(wave_b, new_speaker, self[cluster].gender )
                            match_voice_wrapper(cluster, wave_b+'.mfcc', new_speaker, self[cluster].gender)                            
                            b_s = self[cluster].get_best_speaker()
                            
                            print 'b_s = %s   new_speaker = %s ' % ( b_s, new_speaker )
                            
                            if b_s != new_speaker :
                                print "removing model for speaker %s" % (old_speaker)
                                self.get_db().remove_model( os.path.join( wave_dir, cluster) + '.mfcc', old_speaker, self[cluster].gender, self[cluster].value )
                                self[cluster].set_speaker(new_speaker)
                                
#                            if old_speaker != "unknown":
#                                results = self.get_db().match_voice( mfcc_name, db_entry, gender)
#                                for r in results:
#                                    self[cluster].add_speaker( r, results[r] )

                            if not keep_intermediate_files:
                                os.remove("%s.gmm" % wave_b )
                                os.remove("%s.wav" % wave_b )
                                os.remove("%s.seg" % wave_b )
                                os.remove("%s.mfcc" % wave_b )
                                os.remove("%s.ident.seg" % wave_b )
                                os.remove("%s.init.gmm" % wave_b )
                            #end build_model_wrapper
                        
                        threads[c] = threading.Thread( target=build_model_wrapper, args=(basename_file,c, basename, old_s) )
                        threads[c].start()
                    
            if not interactive:
                if not quiet: print '\t best speaker: %s (distance from 2nd %f - mean %f - distance from mean %f ) ' % (speakers[c] , distance, mean, m_distance)    
        
        sec = wave_duration( basename+'.wav' )
        total_time = time.time() - start_time
        self.set_time( total_time )
        self._status = 5
        if not quiet: print self.get_working_status()
        if interactive and len(threads) > 0:
            print "Waiting for working processes"
            for t in threads:
                if threads[t].is_alive():
                    threads[t].join()
        if not interactive:
            if not quiet: print "\nwav duration: %s\nall done in %dsec (%s) (diarization %dsec time:%s )  with %s threads and %d voices in db (%f)  " % ( humanize_time(sec), total_time, humanize_time(total_time), diarization_time, humanize_time(diarization_time), thrd_n, len(files_in_db['F'])+len(files_in_db['M'])+len(files_in_db['U']), float(total_time - diarization_time )/len(files_in_db) )

    def to_XMP_string(self):
        """ Return the Adobe XMP representation of the information about who is speaking and when. The tags used are Tracks and Markers, the ones used by Adobe Premiere for speech-to-text information.
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
            inner_string +="""    
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
        #TODO: extract previous XMP information from the media and merge with speaker information
        return initial_tags+inner_string+final_tags            

    
    def to_dict(self):
        """ Return a JSON representation for the clustering information."""
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
                                     "startTime" : float(s[0])/100,
                                     "endTime" : float(s[0]+s[1])/100,
                                     'speaker': s[-2],
                                     'speakerLabel': s[-1],
                                     'gender': s[2]
                                     })
        return d

    def write_json(self,dictionary=None):
        """ Write to file the json dictionary representation of the Clusters"""
        if not dictionary:
            dictionary = self.to_dict()
        prefix = ''
        if self._interactive:
            prefix = '.interactive'
        
        file_json = open(self.get_file_basename()+prefix+'.json','w')
        file_json.write(str(dictionary))
        file_json.close()

    def write_output(self,mode):
        """ Write to file (basename.extension, for example: myfile.srt) the output of   """
        
        if mode == 'srt':
            seg2srt(self.get_file_basename()+'.seg')
            srt2subnames(self.get_file_basename(), self.get_speakers_map()) # build subtitles - the main output at this time
            shutil.move(self.get_file_basename()+'.ident.srt', self.get_file_basename()+'.srt')
            
        if mode == 'json':
            self.write_json()
        
        if mode == 'xmp':
            file_xmp = open(self.get_file_basename()+'.xmp','w')
            file_xmp.write(str(self.to_XMP_string()))
            file_xmp.close()

#-------------------------------------
# initializations and global variables
#-------------------------------------
lium_jar = os.path.expanduser('~/.voiceid/lib/LIUM_SpkDiarization-4.7.jar')  # http://lium3.univ-lemans.fr/diarization/doku.php
ubm_path  = os.path.expanduser('~/.voiceid/lib/ubm.gmm')
test_path  = os.path.expanduser('~/.voiceid/test')
db_dir = os.path.expanduser('~/.voiceid/gmm_db')
output_format = 'srt' #default output format
quiet_mode = False

verbose = False
keep_intermediate_files = False

dev_null = open('/dev/null','w')
if verbose:
        dev_null = None

#-------------------------------------
#  utils
#-------------------------------------
def start_subprocess(commandline):
    """ Start a subprocess using the given commandline and checks for correct termination """
    args = shlex.split(commandline)
    #print commandline
    p = subprocess.Popen(args, stdin=dev_null,stdout=dev_null, stderr=dev_null)
    retval = p.wait()
    if retval != 0:
        raise Exception("Subprocess %s closed unexpectedly [%s]" %  (str(p), commandline) )

def ensure_file_exists(filename):
    """ Ensure file exists and is not empty, otherwise raise an Exception """
    if not os.path.exists(filename):
        raise Exception("File %s doesn't exist or not correctly created"  % filename)
    if not (os.path.getsize(filename) > 0):
        raise Exception("File %s empty"  % filename)

def check_deps():
    """ Check for dependency """
    ensure_file_exists(lium_jar)

    dir_m = os.path.join(db_dir,"M")
    dir_f = os.path.join(db_dir,"F")
    dir_u = os.path.join(db_dir,"U")
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
    """ Convert seconds into time format """
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d,%s' % (hours, mins, int(secs), str(("%0.3f" % secs ))[-3:] )

#-------------------------------------
# wave files management
#-------------------------------------
def wave_duration(wavfile):
    """ Extract the duration of a wave file in sec """
    import wave
    w = wave.open(wavfile)
    par = w.getparams()
    w.close()
    return par[3]/par[2]

def merge_waves(input_waves,wavename):
    """ Take a list of waves and append them all to a brend new destination wave """
    #if os.path.exists(wavename):
            #raise Exception("File gmm %s already exist!" % wavename)
    waves = [w.replace(" ","\ ") for w in input_waves]
    w = " ".join(waves)
    commandline = "sox "+str(w)+" "+ str(wavename)
    start_subprocess(commandline)

def video2wav(file_name):
    """ Take any kind of video or audio and convert it to a "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz" wave file using gstreamer. If you call it passing a wave it checks if in good format, otherwise it converts the wave in the good format """
    def is_bad_wave(file_name):
        """ Check if the wave is in correct format for LIUM required input file """
        import wave
        par = None
        try:
            w = wave.open(file_name)
            par = w.getparams()
            w.close()
        except Exception,e:
            print e
            return True
        if par[:3] == (1,2,16000) and par[-1:] == ('not compressed',):
            return False
        else:
            return True

    name, ext = os.path.splitext(file_name)
    if ext != '.wav' or is_bad_wave(file_name):
        start_subprocess( "gst-launch filesrc location='"+file_name+"' ! decodebin ! audioresample ! 'audio/x-raw-int,rate=16000' ! audioconvert ! 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1' ! wavenc ! filesink location="+name+".wav " )
    ensure_file_exists(name+'.wav')

#-------------------------------------
# gmm files management
#-------------------------------------
def merge_gmms(input_files,output_file):
    """ Merge two or more gmm files to a single gmm file with more voice models."""
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
    """ Return gender for a gmm file """
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
    """ Split a gmm file into gmm files with a single voice model"""
    def read_gaussian(f):
        g_key = f.read(8)     #read string of 8bytes kind
        if g_key != 'GAUSS___':
            raise Exception("Error: the gaussian is not of GAUSS___ key  (%s)" % g_key)
        g_id = f.read(4)
        g_length = f.read(4)     #readint 4bytes representing the name length
        g_name = f.read( int( struct.unpack('>i',   g_length )[0] )  )
        g_gender = f.read(1)
        g_kind = f.read(4)
        g_dim = f.read(4)
        g_count = f.read(4)
        g_weight = f.read(8)

        dimension = int( struct.unpack('>i',   g_dim )[0] )

        g_header = g_key + g_id + g_length + g_name + g_gender + g_kind + g_dim + g_count + g_weight

#        data = ''
        datasize = 0
        if g_kind == FULL:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < dimension :
                    datasize += 1
                    t+=1
        else:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < j+1 :
                    datasize += 1
                    t+=1

        return g_header + f.read(datasize * 8)

    def read_gaussian_container(f):
        #gaussian container
        ck = f.read(8)    #read string of 8bytes
        if ck != "GAUSSVEC":
            raise Exception("Error: the gaussian container is not of GAUSSVEC kind %s" % ck)
        cs = f.read(4)    #readint 4bytes representing the size of the gaussian container
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
        h = f.read(4)     #readint 4bytes representing the hash (backward compatibility)
        l = f.read(4)     #readint 4bytes representing the name length
        name = f.read( int( struct.unpack('>i',   l )[0] )  ) #read string of l bytes
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
            newname = os.path.join( basedir, "%s%04d.gmm" % (filename, index) )
        fd = open( newname, 'w' )
        fd.write( main_header + f['header'] + f['content'] )
        fd.close()
        index += 1
        

def rename_gmm(input_file,new_name_gmm_file):
    """ Rename a gmm with a new speaker identifier (name)  associated""" 
    
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
    

def build_gmm(file_basename,name):
    """ Build a gmm (Gaussian Mixture Model) file from a given wave with a speaker identifier (name)  associated """

    diarization(file_basename)

    ident_seg(file_basename,name)

    extract_mfcc(file_basename)

    train_init(file_basename)

    train_map(file_basename)

#-------------------------------------
#   seg files and trim functions
#-------------------------------------
def seg2trim(segfile):
    """ Take a wave and splits it in small waves in this directory structure <file base name>/<cluster>/<cluster>_<start time>.wav """
    basename = os.path.splitext(segfile)[0]
    s = open(segfile,'r')
    for line in s.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            clust = arr[7]
            st = float(arr[2])/100
            end = float(arr[3])/100
            try:
                mydir = os.path.join(basename, clust)
                os.makedirs( mydir )
            except os.error as e:
                if e.errno == 17:
                    pass
                else:
                    raise os.error
            wave_path = os.path.join( basename, clust, "%s_%07d.%07d.wav" % (clust, int(st), int(end) ) )
            commandline = "sox %s.wav %s trim  %s %s" % ( basename, wave_path, st, end )
            start_subprocess(commandline)
            ensure_file_exists( wave_path )
    s.close()

def seg2srt(segfile):
    """ Take a seg file and convert it in a subtitle file (srt) """
    def readtime(aline):
        return int(aline[2])

    basename = os.path.splitext(segfile)[0]
    s = open(segfile,'r')
    lines = []
    for line in s.readlines():
        if not line.startswith(";;"):
            arr=line.split()
            lines.append(arr)
    s.close()

    lines.sort(key=readtime, reverse=False)
    fileoutput = basename+".srt"
    srtfile = open(fileoutput,"w")
    row = 0
    for line in lines:
        row = row +1
        st = float(line[2])/100
        en = st+float(line[3])/100
        srtfile.write(str(row)+"\n")
        srtfile.write(humanize_time(st) + " --> " + humanize_time(en) +"\n")
        srtfile.write(line[7]+"\n")
        srtfile.write(""+"\n")

    srtfile.close()
    ensure_file_exists(basename+'.srt')

def extract_mfcc(file_basename):
    """ Extract audio features from the wave file, in particular the mel-frequency cepstrum using a sphinx tool """
    commandline = "sphinx_fe -verbose no -mswav yes -i %s.wav -o %s.mfcc" %  ( file_basename, file_basename )
    start_subprocess(commandline)
    ensure_file_exists(file_basename+'.mfcc')

def ident_seg(filebasename,name):
    """ Substitute cluster names with speaker names ang generate a "<filebasename>.ident.seg" file """
    ident_seg_rename(filebasename,name,filebasename+'.ident')

def ident_seg_rename(filebasename,name,outputname):
    """ Take a seg file and substitute the clusters with a given name or identifier """
    f = open(filebasename+'.seg','r')
    clusters=[]
    lines = f.readlines()
    for line in lines:
        for k in line.split():
            if k.startswith('cluster:'):
                c = k.split(':')[1]
                clusters.append(c)
    f.close()
    output = open(outputname+'.seg', 'w')
    clusters.reverse()
    for line in lines:
        for c in clusters:
            line = line.replace(c,name)
        output.write(line+'\n')
    output.close()
    ensure_file_exists(outputname+'.seg')

def manage_ident(filebasename, gmm, clusters):
    """ Take all the files created by the call of mfcc_vs_gmm() on the whole speakers db and put all the results in a bidimensional dictionary """
    f = open("%s.ident.%s.seg" % (filebasename,gmm ) ,"r")
    for l in f:
        if l.startswith(";;"):
            cluster, speaker = l.split()[ 1 ].split(':')[ 1 ].split('_')
            i = l.index('score:'+speaker) + len('score:'+speaker+" = ")
            ii = l.index(']',i) -1
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
        os.remove("%s.ident.%s.seg" % (filebasename,gmm ) )

def extract_clusters(filename, clusters):
    """ Read _clusters from segmentation file """
    f = open(filename,"r")
    last_cluster = None
    for l in f:
        if l.startswith(";;"):
            speaker_id = l.split()[1].split(':')[1]
            clusters[ speaker_id ] = Cluster(name=speaker_id, gender='U', frames=0, dirname=os.path.splitext(filename)[0] )
            last_cluster = clusters[ speaker_id ]
            last_cluster._seg_header = l
        else:
            line = l.split()
            last_cluster._segments.append( Segment(line) )
            last_cluster._frames += int(line[3])
            last_cluster.gender =  line[4]
            last_cluster._e =  line[5]
    f.close()

def srt2subnames(filebasename, key_value):
    """ Substitute cluster names with real names in subtitles """

    def replace_words(text, word_dic):
        """
        take a text and replace words that match a key in a dictionary with
        the associated value, return the changed text
        """
        rc = re.compile('|'.join(map(re.escape, word_dic)))

        def translate(match):
            return word_dic[match.group(0)]+'\n'

        return rc.sub(translate, text)

    file_original_subtitle = open(filebasename+".srt")
    original_subtitle = file_original_subtitle.read()
    file_original_subtitle.close()
    key_value = dict(map(lambda (key, value): (str(key)+"\n", value), key_value.items()))
    text = replace_words(original_subtitle, key_value)
    out_file = filebasename+".ident.srt"
    # create a output file
    fout = open(out_file, "w")
    fout.write(text)
    fout.close()
    ensure_file_exists(out_file)

def video2trim(videofile):
    """ Take a video or audio file and converts it into smaller waves according to the diarization process """
    if not quiet_mode: print "*** converting video to wav ***"
    video2wav(videofile)
    file_basename = os.path.splitext(videofile)[0]
    if not quiet_mode: print "*** diarization ***"
    diarization(file_basename)
    if not quiet_mode: print "*** trim ***"
    seg2trim(file_basename+'.seg')

#--------------------------------------------
#   diarization and voice matching functions
#--------------------------------------------
def diarization(filebasename):
    """ Take a wave file in the correct format and build a segmentation file. The seg file shows how much speakers are in the audio and when they talk """
    start_subprocess( 'java -Xmx2024m -jar '+lium_jar+' --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering ' +  filebasename )
    ensure_file_exists(filebasename+'.seg')

def train_init(file_basename):
    """ Train the initial speaker gmm model """
    commandline = 'java -Xmx256m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=%s.ident.seg --fInputMask=%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask='+ubm_path+' --tOutputMask=%s.init.gmm '+file_basename
    start_subprocess(commandline)
    ensure_file_exists(file_basename+'.init.gmm')

def train_map(file_basename):
    """ Train the speaker model using a MAP adaptation method """
    commandline = 'java -Xmx256m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=%s.ident.seg --fInputMask=%s.mfcc --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm ' + file_basename 
    start_subprocess(commandline)
    ensure_file_exists(file_basename+'.gmm')

def mfcc_vs_gmm(filebasename, gmm, gender,custom_db_dir=None):
    """ Match a mfcc file and a given gmm model file """
    database = db_dir
    if custom_db_dir != None:
        database = custom_db_dir
    gmm_name = os.path.split(gmm)[1]
    commandline = 'java -Xmx256M -Xms256M -cp ' + lium_jar + '  fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg   --fInputMask=%s.mfcc  --sOutputMask=%s.ident.' + gender + '.' + gmm_name + '.seg --sOutputFormat=seg,UTF8  --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:0:300:4" --tInputMask=' + database + '/' + gender + '/' + gmm + ' --sTop=8,' + ubm_path + '  --sSetLabel=add --sByCluster ' + filebasename 
    start_subprocess(commandline)
    ensure_file_exists(filebasename + '.ident.' + gender + '.' + gmm_name + '.seg')
    
#def threshold_tuning():
#    """ Get a score to tune up the threshold to define when a speaker is unknown"""
#    filebasename = os.path.join(test_path,'mr_arkadin')
#    gmm = "mrarkadin.gmm"
#    gender = 'M'
#    ensure_file_exists(filebasename+'.wav')
#    ensure_file_exists( os.path.join(test_path,gender,gmm ) )
#    video2trim(filebasename+'.wav')
#    extract_mfcc(filebasename)
#    mfcc_vs_gmm(filebasename, gmm, gender,custom_db_dir=test_path)
#    clusters = {}
#    extract_clusters(filebasename+'.seg',clusters)
#    manage_ident(filebasename,gender+'.'+gmm,clusters)
#    return clusters['S0'].speakers['mrarkadin']

def interactive_training(videoname, cluster, speaker):
    """ A user interactive way to set the name to an unrecognized voice of a given cluster """
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
            videocluster = str(videoname+"/"+cluster)
            listwaves = os.listdir(videocluster)
            listw = [os.path.join(videocluster, f) for f in listwaves]
            w = " ".join(listw)
            commandline = "play "+str(w)
            print "  Listening %s..." % cluster
            args = shlex.split(commandline)
            p = subprocess.Popen(args, stdin=dev_null, stdout=dev_null, stderr=dev_null)
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

def multiargs_callback(option, opt_str, value, parser):
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
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g INPUT_FILE
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g WAVE WAVE ... WAVE  MERGED_WAVES """

    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="verbose mode")
    parser.add_option("-q", "--quiet", dest="quiet_mode", action="store_true", default=False, help="suppress prints")
    parser.add_option("-k", "--keep-intermediatefiles", dest="keep_intermediate_files", action="store_true", help="keep all the intermediate files")
    parser.add_option("-i", "--identify",  dest="file_input", metavar="FILE", help="identify speakers in video or audio file")
    parser.add_option("-g", "--gmm", action="callback", callback=multiargs_callback, dest="waves_for_gmm", help="build speaker model ")
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
        if options.output_format not in ('srt','json','xmp'):
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
        default_db = GMMVoiceDB( path=db_dir )
        
        #create voiceid instance
        cmanager = Voiceid( db=default_db, filename=options.file_input )
        
        #extract the speakers
        cmanager.extract_speakers( interactive=options.interactive, quiet=quiet_mode, thrd_n=cpu_count() * 4 )
        
        #write the output according to the given output format
        cmanager.write_output( output_format )
        
        if not keep_intermediate_files:
            os.remove( cmanager.get_file_basename()+'.seg' )            
            os.remove( cmanager.get_file_basename()+'.mfcc' )
            w = cmanager.get_file_basename()+'.wav'
            if cmanager.get_filename() != w:
                os.remove( w )
            shutil.rmtree( cmanager.get_file_basename() )
        exit(0)
        
    if options.waves_for_gmm and options.speakerid:
        file_basename = None
        waves = options.waves_for_gmm
        speaker = options.speakerid
        w = None
        if len(waves)>1:
            merge_waves( waves[:-1], waves[-1] )
            w = waves[-1]
        else:
            w = waves[0]
        basename, extension = os.path.splitext(w)
        file_basename = basename
        build_gmm(file_basename,speaker)
        exit(0)

    parser.print_help()
