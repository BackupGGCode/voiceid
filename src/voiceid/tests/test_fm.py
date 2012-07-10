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

import os
import shutil
import unittest
import filecmp
from voiceid import fm

test_wav = os.path.join('data', 'test', 'mr_arkadin.wav')
two_spkrs_wav = os.path.join('data', 'test', 'twospeakers.wav')
test_wav_b = os.path.splitext(test_wav)[0]
test_gmm = os.path.join('data', 'test', 'db', 'M', 'mrarkadin.gmm')
test_name = 'mrarkadin'


class FMTest(unittest.TestCase):
    """voiceid.fm tests"""
    def test_wave_duration(self):
        self.assertEqual(fm.wave_duration(test_wav), 43)

    def test_get_gender(self):
        self.assertEqual(fm.get_gender(test_gmm), 'M')

    def test_extract_mfcc(self):
        fm.extract_mfcc(test_wav_b)
        os.remove(test_wav_b + '.mfcc')

    def test_diarization_standard(self):
        filebasename = os.path.splitext(two_spkrs_wav)[0]
        fm.diarization_standard(filebasename)

    def test_diarization(self):
        filebasename = os.path.splitext(two_spkrs_wav)[0]
        fm.extract_mfcc(filebasename)
        fm.diarization(filebasename)

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

if __name__ == "__main__":
    unittest.main()
