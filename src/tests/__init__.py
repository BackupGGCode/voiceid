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
BASE_DIR = os.path.dirname(__file__)
TEST_DIR = os.path.join(BASE_DIR, 'data')
TEMP_DIR = os.path.join(BASE_DIR, 'tmp')
TEST_WAV = os.path.join(TEMP_DIR, 'mr_arkadin.wav')
TEST_WAV_ID_SEG = os.path.join(TEMP_DIR,
                    'mr_arkadin_test.ident.M.mrarkadin.gmm_test.seg')
TWO_SPKRS_WAV = os.path.join(TEMP_DIR, 'twospeakers.wav')
TWO_SPKRS_SEG = os.path.join(TEMP_DIR, 'twospeakers_test.seg')
TWO_SPKRS_SEG_ST = os.path.join(TEMP_DIR, 'twospeakers_test_st.seg')
TEST_WAV_B = os.path.splitext(TEST_WAV)[0]
TEST_GMM = os.path.join(TEMP_DIR, 'db', 'M', 'mrarkadin.gmm')
TEST_NAME = 'mrarkadin'
DB_DIR = os.path.join(TEMP_DIR, 'db')
