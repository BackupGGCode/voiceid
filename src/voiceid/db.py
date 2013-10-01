# -*- coding: utf-8 -*-
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
from decimal import DivisionByZero
"""Module containing the voice DB relative classes."""

from . import sr, utils, fm
import os
import shutil
import threading
import time


class VoiceDB(object):
    """A class that represent a generic voice models db.

    :type path: string
    :param path: the voice db path"""
    def __init__(self, path):
        """
        :type path: string
        :param path: the voice vdb path"""
        self._path = path
        self._genders = ['F', 'M', 'U']
        self._speakermodels = {}
        self._read_db()

    def get_path(self):
        """Get the base path of the voice models db, where are stored the voice
        model files, splitted in 3 directories according
        to the gender (F, M, U).

        :rtype: string
        :returns: the path of the voice db"""
        return self._path

    def get_speakers(self):
        """Return a dictionary where the keys are the genders and the values
        are a list for every gender with the available speakers models."""
        raise NotImplementedError()

    def _read_db(self):
        """Read the db structure"""
        raise NotImplementedError()

    def add_model(self, basefilename, identifier, gender=None, score=None):
        """Add a voice model to the database.

        :type basefilename: string
        :param basefilename: basename including absolulute path of
            the voice file

        :type identifier: string
        :param identifier: name or label of the speaker voice in the model, in
            a single word without special characters

        :type gender: char F, M or U
        :param gender: the gender of the speaker in the model
        
        :type score: float
        :param score: the score obtained in the voice matching
        """
        raise NotImplementedError()

    def remove_model(self, wave_file, identifier, score, gender):
        """Remove a speaker model from the database according to the score it
        gets by matching vs the given feature file

        :type wave_file: string
        :param wave_file: the wave file

        :type identifier: string
        :param identifier: the name or label of the speaker

        :type score: float
        :param score: the score obtained in the voice matching

        :type gender: char F, M or U
        :param gender: the speaker gender"""
        raise NotImplementedError()

    def match_voice(self, wave_file, identifier, gender):
        """Match the given feature file vs the specified speaker model.

        :type wave_file: string
        :param wave_file: the wave file

        :type identifier: string
        :param identifier: the name or label of the speaker

        :type gender: char F, M or U
        :param gender: the speaker gender"""
        raise NotImplementedError()

    def voice_lookup(self, wave_file, gender):
        """Look for the best matching speaker in the db for the given
        features file.

        :type wave_file: string
        :param wave_file: the wave file

        :type gender: char F, M or U
        :param gender: the speaker gender"""
        raise NotImplementedError()

    def voices_lookup(self, wave_dictionary):
        """Look for the best matching speaker in the db for the given features
        files in the dictionary.

        :type wave_dictionary: dictionary
        :param wave_dictionary: a dict where the keys are the wave
                file extracted from the wave, and the values are the relative
                gender (char F, M or U).

        :rtype: dictionary
        :returns: a dictionary having a computed score for every voice model
        in the db"""
        raise NotImplementedError()


class GMMVoiceDB(VoiceDB):
    """A Gaussian Mixture Model voices database.

    :type path: string
    :param path: the voice db path"""

    def __init__(self, path, thrd_n=1):
        VoiceDB.__init__(self, path)
        if not hasattr(self, '__threads'):
            self.__threads = {}  # class field
        self.__maxthreads = thrd_n

    def set_maxthreads(self, trd):
        """Set the max number of threads running together for the lookup task.

        :type t: integer
        :param t: max number of threads allowed to run at the same time."""
        if trd > 0:
            self.__maxthreads = trd

    def _read_db(self):
        """Read for any changes the db voice models files."""
        for gen in self._genders:
            dir_ = []
            path = os.path.join(self._path, gen)
            try:
                dir_ = os.listdir(path)
            except (OSError, IOError):
                os.makedirs(path)
            self._speakermodels[gen] = [f for f in dir_ if f.endswith('.gmm')]

    def add_model(self, basefilename, identifier, gender=None, score=None):
        """Add a gmm model to db.

        :type basefilename: string
        :param basefilename: the wave file basename and path

        :type identifier: string
        :param identifier: the speaker in the wave

        :type gender: char F, M or U
        :param gender: the gender of the speaker (optional)"""

        #fm.extract_mfcc(basefilename)
        #utils.ensure_file_exists(basefilename + ".mfcc")
        #print ("%s,%s" % (basefilename, identifier))
        if identifier == 'unknown':
            return False
        
        fm.build_gmm(basefilename, identifier)
#        try:
#            _silence_segmentation(basefilename)
#        except:
#            return False
        if gender == None:
            def _get_gender_from_seg(segfile):
                """Identify gender from seg file"""
                gen = {'M': 0, 'F': 0, 'U': 0}
                seg = open(segfile, 'r')
                for line in seg.readlines():
                    if not line.startswith(';;'):
                        gen[line.split(' ')[4]] += 1
                seg.close()

                if gen['M'] > gen['F']:
                    return 'M'
                elif gen['M'] < gen['F']:
                    return 'F'
                else:
                    return 'U'
            gender = _get_gender_from_seg(basefilename + '.seg')

#            _gender_detection(basefilename)
#        else:
#            shutil.move(basefilename + '.msg.seg', basefilename + '.seg')
#        ident_seg(basefilename, identifier)
#        _train_init(basefilename)
#        extract_mfcc(basefilename)
#        _train_map(basefilename)

        gmm_path = basefilename + '.gmm'
        orig_gmm = os.path.join(self.get_path(),
                                    gender, identifier + '.gmm')
        folder_db_dir = os.path.join(self.get_path(), gender)
        folder_tmp = os.path.join(folder_db_dir, identifier + "_tmp_gmms")
        #print "add model score first gmm " + str(abs(float(score)))
#        try:
#            utils.ensure_file_exists(orig_gmm)
        if os.path.exists(orig_gmm):
            if not os.path.exists(folder_tmp):
                os.mkdir(folder_tmp)
            fm.split_gmm(os.path.join(folder_db_dir, identifier + ".gmm"),
                      folder_tmp)
            listgmms = os.listdir(folder_tmp)
            for gmm in listgmms:
                fm.wav_vs_gmm(basefilename,
                                        os.path.join(identifier + "_tmp_gmms", gmm),
                                        gender, self.get_path())
                segfile = open("%s.ident.%s.%s.seg" % 
                         (basefilename, gender, gmm), "r")
                
                for line in segfile:
                    if line.startswith(";;"):
                        snm = line.split()[1].split(':')[1].split('_')
                        idx = line.index('score:' + snm[1])
                        idx = idx + len('score:' + snm[1] + " = ")
                        iidx = line.index(']', idx) - 1
                        #print "add model score second gmm " +str(abs(float(line[idx:iidx])))
                        #print "add model score second gmm " + str(score)
                        if abs(abs(float(line[idx:iidx])) - abs(score)) < 0.07:
                            shutil.rmtree(folder_tmp)
                            #print "not added model"
                            return False
                        
            try:
                shutil.rmtree(folder_tmp)
            except:
                pass
            fm.merge_gmms([orig_gmm, gmm_path], orig_gmm)
            self._read_db()
            return True
 #       except IOError, exc:
        else:
            #msg = "File %s doesn't exist or not correctly created" % orig_gmm
            #print msg
            if os.path.exists(folder_tmp):
                shutil.rmtree(folder_tmp)
#            if str(exc) == msg:
            shutil.move(gmm_path, orig_gmm)
            self._read_db()
            return True
        return False

    def remove_model(self, wave_file, identifier, score, gender):
        """Remove a voice model from the db.

        :type wave_file: string
        :param wave_file: the wave file name and path

        :type identifier: string
        :param identifier: the speaker in the wave

        :type score: float
        :param score: the value of

        :type gender: char F, M or U
        :param gender: the gender of the speaker (optional)"""
        folder_db_dir = os.path.join(self.get_path(), gender)
        #print "score first gmm " + str(abs(float(score)))
        if os.path.exists(os.path.join(folder_db_dir, identifier + ".gmm")):
            folder_tmp = os.path.join(folder_db_dir, identifier + "_tmp_gmms")
            if not os.path.exists(folder_tmp):
                os.mkdir(folder_tmp)
            fm.split_gmm(os.path.join(folder_db_dir, identifier + ".gmm"),
                      folder_tmp)
            listgmms = os.listdir(folder_tmp)
            filebasename = os.path.splitext(wave_file)[0]
            removed = False
            if len(listgmms) != 1:
                for gmm in listgmms:
                    fm.wav_vs_gmm(filebasename,
                                os.path.join(identifier + "_tmp_gmms", gmm),
                                gender, self.get_path())
                    segfile = open("%s.ident.%s.%s.seg" % 
                             (filebasename, gender, gmm), "r")
                    
                    for line in segfile:
                        if line.startswith(";;"):
                            snm = line.split()[1].split(':')[1].split('_')
                            idx = line.index('score:' + snm[1])
                            idx = idx + len('score:' + snm[1] + " = ")
                            iidx = line.index(']', idx) - 1
                            #print "multiple score second gmm " + str(abs(float(line[idx:iidx])))
                            #print "multiple score second gmm " + str(score)
                            #if abs(abs(s_score) - abs(c_s_score)) < 0.07:
                            
                            if abs(abs(float(line[idx:iidx])) - abs(score)) < 0.07:
                                #print "removeeed"
                                os.remove(os.path.join(folder_tmp, gmm))
                                removed = True
                listgmms_path = []
                listgmms = os.listdir(folder_tmp)
                for gmm in listgmms:
                    listgmms_path.append(os.path.join(folder_tmp, gmm))
                fm.merge_gmms(listgmms_path,
                           os.path.join(folder_db_dir, identifier + ".gmm"))
            else:
                for gmm in listgmms:
#                    print (filebasename,
#                                    os.path.join(identifier + "_tmp_gmms", gmm),
#                                    gender, self.get_path())
                    fm.wav_vs_gmm(filebasename,
                                    os.path.join(identifier + "_tmp_gmms", gmm),
                                    gender, self.get_path())
                    segfile = open("%s.ident.%s.%s.seg" % 
                             (filebasename, gender, gmm), "r")
                    for line in segfile:
                        if line.startswith(";;"):
                            snm = line.split()[1].split(':')[1].split('_')
                            idx = line.index('score:' + snm[1])
                            idx = idx + len('score:' + snm[1] + " = ")
                            iidx = line.index(']', idx) - 1
                            #print "score second gmm " + str(float(line[idx:iidx]))
                            #print "score second gmm " + str(score)
                            if str(float(line[idx:iidx])) == str(score):
                                #print "removeeed"
                                os.remove(os.path.join(folder_db_dir, identifier + ".gmm"))
                                removed = True
                
            shutil.rmtree(folder_tmp)
            self._read_db()
            return removed

    def match_voice(self, wave_file, identifier, gender):
        """Match the voice (wave file) versus the gmm model of
        'identifier' in db.

        :type wave_file: string
        :param wave_file: wave file extracted from the wave

        :type identifier: string
        :param identifier: the speaker in the wave

        :type gender: char F, M or U
        :param gender: the gender of the speaker (optional)"""

        wave_basename = os.path.splitext(wave_file)[0]
        try:
#            print "match_voice"
#            print (wave_basename, identifier + '.gmm',
#                          gender, self.get_path())
            fm.wav_vs_gmm(wave_basename, identifier + '.gmm',
                         gender, self.get_path())
#             print "after wav_vs_gmm"
            
            cls = {}
            sr.manage_ident(wave_basename,
                      gender + '.' + identifier + '.gmm', cls)
            
        except  DivisionByZero: #ValueError, e:
            print "ValueError in MATCH_VOICE"
            print "tring to fix... ", #(wave_basename, identifier + '.gmm',
                     # gender, self.get_path())
            raise e         
            fm._train_init(wave_basename)
            fm._train_map(wave_basename)
            fm.diarization(wave_basename)
        
            fm.wav_vs_gmm(wave_basename, identifier + '.gmm',
                     gender, self.get_path())
            cls = {}
            sr.manage_ident(wave_basename,
                      gender + '.' + identifier + '.gmm', cls)
        
        
        spkrs = {}
        for clust in cls:
            spkrs.update(cls[clust].speakers)
        return spkrs

    def get_speakers(self):
        """Return a dictionary where the keys are the genders and the values
        are a list of the available speakers models for every gender."""
        result = {}
        for gen in self._genders:
            result[gen] = [os.path.splitext(m)[0]
                         for m in self._speakermodels[gen]]
        return result

    def voice_lookup(self, wave_file, gender):
        """Look for the best matching speaker in the db for the given
        features file.

        :type wave_file: string
        :param wave_file: the wave file

        :type gender: char F, M or U
        :param gender: the speaker gender

        :rtype: dictionary
        :returns: a dictionary having a computed score for every voice
                model in the db """
        speakers = self.get_speakers()[gender]
        res = {}
        out = {}

        def _match_voice(self, wave_file, speaker, gender):
            """Internal routine to run in a Thread"""
            out[speaker + wave_file + gender] = self.match_voice(wave_file,
                                                                 speaker,
                                                                 gender)

        keys = []

        for spk in speakers:
            out[spk + wave_file + gender] = None
            if  utils.alive_threads(self.__threads) < self.__maxthreads:
                keys.append(spk + wave_file + gender)
                self.__threads[spk + wave_file + gender] = threading.Thread(
                                            target=_match_voice,
                                            args=(self, wave_file, spk, gender))
                self.__threads[spk + wave_file + gender].start()
            else:
                while utils.alive_threads(self.__threads) >= self.__maxthreads:
                    time.sleep(1)
                keys.append(spk + wave_file + gender)
                self.__threads[spk + wave_file + gender] = threading.Thread(
                                      target=_match_voice,
                                      args=(self, wave_file, spk, gender))
                self.__threads[spk + wave_file + gender].start()

        for thr in keys:
            if self.__threads[thr].is_alive():
                self.__threads[thr].join()
            res.update(out[thr])

        return res

    def voices_lookup(self, wave_dictionary):
        """Look for the best matching speaker in the db for the given features
         files in the dictionary.

        :type wave_dictionary: dictionary
        :param wave_dictionary: a dict where the keys are the wave, and the values are the relative
               gender (char F, M or U).

        :rtype: dictionary
        :returns: a dictionary having a computed score for every voice
                 model in the db"""

        out = {}
        res = {}
        keys = []

        def __match_voice(self, wave_file, speaker, gender):
            """Internal routine to run in a Thread"""
            try:
                speakerkey = wave_file + '***' + speaker + gender
                out[speakerkey] = self.match_voice(wave_file, speaker, gender)
                
            except (OSError, IOError):
                exit(-1)

        for wave_file in wave_dictionary:
            gender = wave_dictionary[wave_file]
            speakers = self.get_speakers()[gender]
            from voiceid.utils import alive_threads as alive
            for spk in speakers:
                speakerkey = wave_file + '***' + spk + gender
                out[speakerkey] = None
                if  alive(self.__threads) < self.__maxthreads:
                    keys.append(speakerkey)
                    self.__threads[speakerkey] = threading.Thread(
                                          target=__match_voice,
                                          args=(self, wave_file, spk, gender))
                    self.__threads[speakerkey].start()
                else:
                    while alive(self.__threads) >= self.__maxthreads:
                        time.sleep(1)
                    keys.append(speakerkey)
                    self.__threads[speakerkey] = threading.Thread(
                                          target=__match_voice,
                                          args=(self, wave_file, spk, gender))
                    self.__threads[speakerkey].start()
        for thr in keys:
            if self.__threads[thr].is_alive():
                self.__threads[thr].join()
        for thr in out:
            arr = out[thr]
            wave_key = thr.split('***')[0]
            if not wave_key in res: # "old" res.has_key(mfcc_key)
                res[wave_key] = {}
            try:
                c = res[wave_key]
                
            except (NameError , KeyError, AttributeError, TypeError), e:
                
                print " c = res[wave_key] missing out[" + thr + "]"
                print e
                print e.__dict__
                print e.args
            try:
                c.update(arr)
                
            except (NameError , KeyError, AttributeError, TypeError), e:
                
                print "c.update(arr) missing out[" + thr + "]"
                print e
                print c
                print "arr " + str(arr)
                print e.__dict__
                print e.args
            try:
                res[wave_key] = c
                
            except (NameError , KeyError, AttributeError, TypeError), e:
                
                print "res[wave_key] = c missing out[" + thr + "]"
                print e
                print e.__dict__
                print e.args
            
        return res
