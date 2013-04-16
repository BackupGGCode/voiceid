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

from tests import TEMP_DIR, TEST_DIR, TEST_WAV, TEST_NAME, TEST_GMM, \
    TWO_SPKRS_WAV, TWO_SPKRS_SEG, TWO_SPKRS_SEG_ST, TEST_WAV_B, \
    DB_DIR, TEST_WAV_ID_SEG
from voiceid import fm
import filecmp
import os
import shutil
import unittest


def setUpModule():
    if os.path.isdir(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    shutil.copytree(TEST_DIR, TEMP_DIR)


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
        newname = TEST_WAV.replace('_', '')
        shutil.copy(TEST_WAV, newname)
        newname = os.path.splitext(newname)[0]
        fm.build_gmm(newname, TEST_NAME)
        self.assertTrue(filecmp.cmp(newname + '.gmm', TEST_GMM))

    def test_diarization(self):
        filebasename = os.path.splitext(TWO_SPKRS_WAV)[0]
        fm.diarization(filebasename)
        self.assertTrue(compare_seg(filebasename + '.seg', TWO_SPKRS_SEG))

    def test_diarization_standard(self):
        filebasename = os.path.splitext(TWO_SPKRS_WAV)[0]
        fm.diarization_standard(filebasename)
        self.assertTrue(compare_seg(filebasename + '.seg', TWO_SPKRS_SEG_ST))

    def test_get_gender(self):
        self.assertEqual(fm.get_gender(TEST_GMM), 'M')

    def test_wav_vs_gmm(self):
        gmm_file = TEST_GMM.split(os.path.sep)[-1]
        wav_filename = TEST_WAV_B.split(os.path.sep)[-1]
        fm.wav_vs_gmm(TEST_WAV_B, gmm_file, 'M', custom_db_dir=DB_DIR)
        ident_seg = os.path.join(TEMP_DIR,
                    wav_filename + '.ident.M.' + gmm_file + '.seg')
        self.assertTrue(compare_seg(ident_seg, TEST_WAV_ID_SEG, True))

    def test_wave_duration(self):
        self.assertEqual(fm.wave_duration(TEST_WAV), 43)

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(FMTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
