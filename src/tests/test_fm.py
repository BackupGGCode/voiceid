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

from voiceid import fm
import filecmp
import os
import shutil
import unittest

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
test_dir = DATA_DIR
temp_dir = os.path.join(os.path.dirname(__file__), 'tmp')
test_wav = os.path.join(temp_dir, 'mr_arkadin.wav')
test_mfcc = os.path.join(temp_dir, 'mr_arkadin_test.mfcc')
test_mfcc_b = os.path.splitext(test_mfcc)[0]
test_mfcc_id_seg = os.path.join(temp_dir, 
                    'mr_arkadin_test.ident.M.mrarkadin.gmm_test.seg')
two_spkrs_wav = os.path.join(temp_dir, 'twospeakers.wav')
two_spkrs_seg = os.path.join(temp_dir, 'twospeakers_test.seg')
two_spkrs_seg_st = os.path.join(temp_dir, 'twospeakers_test_st.seg')
test_wav_b = os.path.splitext(test_wav)[0]
test_gmm = os.path.join(temp_dir, 'db', 'M', 'mrarkadin.gmm')
test_name = 'mrarkadin'
db_dir = os.path.join(temp_dir, 'db')


def setUpModule():
    if os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
    shutil.copytree(test_dir, temp_dir)


def compare_seg(seg_1, seg_2, headers=False):
    def clean_string_array(myarr, headers=False):
        newarr = []
        for line in myarr:
            if headers or not line.startswith(';;'):
                tmp = line.split()[1:]
                newarr.append(" ".join(tmp))
        return newarr
    sof1 = open(seg_1)
    sof2 = open(seg_2)
    sd1 = sof1.readlines()
    sd2 = sof2.readlines()
    sof1.close()
    sof2.close()
    sd1 = clean_string_array(sd1, headers)
    sd2 = clean_string_array(sd2, headers)
    if len(sd1) != len(sd2):
        return False
#    for i in range(len(sd1)):
#        print "%s *** %s" % (sd1[i], sd2[i])
    interc = set(sd1).intersection(set(sd2))
    if len(interc) != len(sd1):
        return False
    return True


class FMTest(unittest.TestCase):
    """voiceid.fm tests"""

    def test_build_gmm(self):
        newname = test_wav.replace('_', '')
        shutil.copy(test_wav, newname)
        newname = os.path.splitext(newname)[0]
        try:
            shutil.rmtree(newname + '.mfcc')
        except:
            pass
        fm.build_gmm(newname, test_name)
        self.assertTrue(filecmp.cmp(newname + '.gmm', test_gmm))

    def test_diarization(self):
        filebasename = os.path.splitext(two_spkrs_wav)[0]
        fm.extract_mfcc(filebasename)
        fm.diarization(filebasename)
        self.assertTrue(compare_seg(filebasename + '.seg', two_spkrs_seg))

    def test_diarization_standard(self):
        filebasename = os.path.splitext(two_spkrs_wav)[0]
        fm.diarization_standard(filebasename)
        self.assertTrue(compare_seg(filebasename + '.seg', two_spkrs_seg_st))

    def test_extract_mfcc(self):
        fm.extract_mfcc(test_wav_b)
        self.assertTrue(filecmp.cmp(test_wav_b + '.mfcc', test_mfcc))

    def test_get_gender(self):
        self.assertEqual(fm.get_gender(test_gmm), 'M')

    def test_get_features_number(self):
        test_mfcc_b = os.path.splitext(test_mfcc)[0]
        self.assertEqual(fm.get_features_number(test_mfcc_b), 4305)

    def test_mfcc_vs_gmm(self):
        gmm_file = test_gmm.split(os.path.sep)[-1]
        mfcc_filename = test_mfcc_b.split(os.path.sep)[-1]
        if not os.path.isfile(test_mfcc_b + '.seg'):
            fm.generate_uem_seg(test_mfcc_b)
            os.rename(test_mfcc_b + '.uem.seg', test_mfcc_b + '.seg')
        fm.mfcc_vs_gmm(test_mfcc_b, gmm_file, 'M', custom_db_dir=db_dir)
        ident_seg = os.path.join(temp_dir,
                    mfcc_filename + '.ident.M.' + gmm_file + '.seg')
        self.assertTrue(compare_seg(ident_seg, test_mfcc_id_seg, True))

    def test_wave_duration(self):
        self.assertEqual(fm.wave_duration(test_wav), 43)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(FMTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
