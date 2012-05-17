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

import os
import shutil
import time
from threading import Thread
from sr import manage_ident
from utils import ensure_file_exists, alive_threads
from fm import extract_mfcc, build_gmm, merge_gmms, split_gmm, \
    mfcc_vs_gmm

#-------------------------------------
#   classes
#-------------------------------------
class VoiceDB:
    """A class that represent a generic voice models db.
    
    :type path: string
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
        """Get the base path of the voice models db, where are stored the voice model 
        files, splitted in 3 directories according to the gender (F, M, U).
        
        :rtype: string
        :returns: the path of the voice db
        """
        return self._path
    
    def get_speakers(self):
        """Return a dictionary where the keys are the genders and the values 
        are a list for every gender with the available speakers models."""
        raise NotImplementedError()
    
    def _read_db(self):
        raise NotImplementedError()
    
    def add_model(self, basefilename, identifier, gender=None):
        """
        Add a voice model to the database.
        
        :type basefilename: string
        :param basefilename: basename including absolulute path of the voice file
        
        :type identifier: string
        :param identifier: name or label of the speaker voice in the model, in a single word without special characters
        
        :type gender: char F, M or U
        :param gender: the gender of the speaker in the model 
        """
        raise NotImplementedError()
    
    def remove_model(self, mfcc_file, identifier, score, gender):
        """
        Remove a speaker model from the database according to the score it gets
        by matching vs the given feature file 
        
        :type mfcc_file: string
        :param mfcc_file: the feature(mfcc) file extracted from the wave
        
        :type identifier: string
        :param identifier: the name or label of the speaker
        
        :type score: float 
        :param score: the score obtained in the voice matching
        
        :type gender: char F, M or U
        :param gender: the speaker gender 
        """
        raise NotImplementedError() 
    
    def match_voice(self, mfcc_file, identifier, gender):
        """
        Match the given feature file vs the specified speaker model.

        :type mfcc_file: string         
        :param mfcc_file: the feature(mfcc) file extracted from the wave
        
        :type identifier: string
        :param identifier: the name or label of the speaker
        
        :type gender: char F, M or U
        :param gender: the speaker gender 
        """
        raise NotImplementedError()
    
    def voice_lookup(self, mfcc_file, gender):
        """
        Look for the best matching speaker in the db for the given features file. 
        
        :type mfcc_file: string         
        :param mfcc_file: the feature(mfcc) file extracted from the wave
        
        :type gender: char F, M or U
        :param gender: the speaker gender 
        """
        raise NotImplementedError() 
        
    def voices_lookup(self, mfcc_dictionary):
        """Look for the best matching speaker in the db for the given features files in the dictionary. 
        
        :type mfcc_dictionary: dictionary
        :param mfcc_dictionary: a dict where the keys are the feature(mfcc) file extracted from the wave, and the values are the relative gender (char F, M or U). 

        :rtype: dictionary
        :returns: a dictionary having a computed score for every voice model in the db 
        """
        raise NotImplementedError()
    
    
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
        """Set the max number of threads running together for the lookup task.
        
        :type t: integer
        :param t: max number of threads allowed to run at the same time.
        """
        if t > 0:
            self.__maxthreads = t
    
    def _read_db(self):
        """Read for any changes the db voice models files."""
        self._speakermodels = {}
        for g in self._genders:
            dir_ = []
            path = os.path.join(self._path, g)
            try:
                dir_ = os.listdir(path)
            except:
                os.makedirs(path)
            self._speakermodels[g] = [ f for f in dir_ if f.endswith('.gmm') ]
    
    def add_model(self, basefilename, identifier, gender=None):
        """Add a gmm model to db.
        
        :type basefilename: string
        :param basefilename: the wave file basename and path

        :type identifier: string
        :param identifier: the speaker in the wave

        :type gender: char F, M or U
        :param gender: the gender of the speaker (optional)"""
                
        extract_mfcc(basefilename)
        
        ensure_file_exists(basefilename+".mfcc")
        build_gmm(basefilename, identifier)
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
#        ident_seg(basefilename, identifier)
#        _train_init(basefilename)
#        extract_mfcc(basefilename)
#        _train_map(basefilename)
        
        gmm_path = basefilename + '.gmm'
        orig_gmm = os.path.join(self.get_path(), 
                                    gender, identifier + '.gmm')
        try:
            ensure_file_exists(orig_gmm)
            merge_gmms([orig_gmm, gmm_path], orig_gmm)
            self._read_db()
            return True
        except IOError,e:
            s = "File %s doesn't exist or not correctly created" % orig_gmm
            if str(e) == s:
                shutil.move(gmm_path, orig_gmm)
                self._read_db()
                return True
        return False
    
    def remove_model(self, mfcc_file, identifier, score, gender):
        """Remove a voice model from the db.

        :type mfcc_file: string
        :param mfcc_file: the mfcc file name and path
        
        :type identifier: string
        :param identifier: the speaker in the wave
        
        :type score: float
        :param score: the value of

        :type gender: char F, M or U         
        :param gender: the gender of the speaker (optional)"""
        old_s = identifier
        
        folder_db_dir = os.path.join(self.get_path(),gender)
        
        if os.path.exists(os.path.join(folder_db_dir, old_s + ".gmm")):
            folder_tmp = os.path.join(folder_db_dir, old_s + "_tmp_gmms")
            if not os.path.exists(folder_tmp):
                os.mkdir(folder_tmp)
                
            split_gmm(os.path.join(folder_db_dir, old_s + ".gmm"), 
                      folder_tmp)
            listgmms = os.listdir(folder_tmp)
            filebasename = os.path.splitext(mfcc_file)[0]
            value_old_s = score
            
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
             
    def match_voice(self, mfcc_file, identifier, gender):
        """Match the voice (mfcc file) versus the gmm model of 
        'identifier' in db.
        
        :type mfcc_file: string
        :param mfcc_file: the feature(mfcc) file extracted from the wave

        :type identifier: string
        :param identifier: the speaker in the wave
        
        :type gender: char F, M or U         
        :param gender: the gender of the speaker (optional)"""
        
        mfcc_basename = os.path.splitext(mfcc_file)[0]
                
        mfcc_vs_gmm( mfcc_basename , identifier + '.gmm', 
                     gender, self.get_path() )
        cls = {}
        manage_ident( mfcc_basename, 
                      gender + '.' + identifier + '.gmm', cls )
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
        
        :rtype: dictionary
        :returns: a dictionary having a computed score for every voice model in the db 
        """
        speakers =  self.get_speakers()[gender]
        res = {}
        out = {}
        
        def match_voice(self, mfcc_file, speaker, gender):
            out[speaker+mfcc_file+gender] = self.match_voice(mfcc_file, speaker, gender)
        
        keys = []
        
        for s in speakers:
            out[s+mfcc_file+gender] = None
            if  alive_threads(self.__threads)  < self.__maxthreads :
                keys.append(s+mfcc_file+gender)
                self.__threads[s+mfcc_file+gender] = Thread(target=match_voice, 
                                      args=(self, mfcc_file, s, gender ) )
                self.__threads[s+mfcc_file+gender].start()
            else:
                while alive_threads(self.__threads) >= self.__maxthreads:
                    time.sleep(1)
                keys.append(s+mfcc_file+gender)
                self.__threads[s+mfcc_file+gender] = Thread(target=match_voice, 
                                      args=(self, mfcc_file, s, gender ) )
                self.__threads[s+mfcc_file+gender].start()                


            
        for thr in keys:
            if self.__threads[thr].is_alive():
                self.__threads[thr].join()
            res.update( out[thr] )    
            
        return res
    
    def voices_lookup(self, mfcc_dictionary):
        """Look for the best matching speaker in the db for the given features files in the dictionary. 
        
        :type mfcc_dictionary: dictionary
        :param mfcc_dictionary: a dict where the keys are the feature(mfcc) file extracted from the wave, and the values are the relative gender (char F, M or U). 

        :rtype: dictionary
        :returns: a dictionary having a computed score for every voice model in the db 
        """
        
        out = {}
        res = {}
        keys = []
        
        def __match_voice(self, mfcc_file, speaker, gender):
#            print "started thread "+speaker+mfcc_file+gender #+" in out["+mfcc_file+"]"
            try:
                speakerkey = mfcc_file+'***'+speaker+gender
                out[speakerkey] = self.match_voice(mfcc_file, speaker, gender)
            except:
                exit(-1)
                
        for mfcc_file in mfcc_dictionary:
            gender = mfcc_dictionary[mfcc_file]
            speakers = self.get_speakers()[gender]
                                    
            #out[mfcc_file] = {}
            for s in speakers:
                speakerkey = mfcc_file+'***'+s+gender 
                out[speakerkey] = None
                if  alive_threads(self.__threads)  < self.__maxthreads :
                    keys.append(speakerkey)
                    self.__threads[speakerkey] = Thread(target=__match_voice, 
                                          args=(self, mfcc_file, s, gender ) )
                    self.__threads[speakerkey].start()
                else:
                    while alive_threads(self.__threads) >= self.__maxthreads:
                        time.sleep(1)
                    keys.append(speakerkey)
                    self.__threads[speakerkey] = Thread(target=__match_voice, 
                                          args=(self, mfcc_file, s, gender ) )
                    self.__threads[speakerkey].start()                
            
        for thr in keys:
            if self.__threads[thr].is_alive():
                self.__threads[thr].join()
        for thr in out:
            arr = out[thr]
            mfcc_key = thr.split('***')[0]
            if not res.has_key(mfcc_key):
                res[mfcc_key] = {}
            try:
                res[mfcc_key].update( arr )
            except:
                print "missing out["+thr+"]"    
            
        return res