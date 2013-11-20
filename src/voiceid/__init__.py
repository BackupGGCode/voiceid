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
"""
VoiceID is a speaker recognition/identification system written in Python,
based on the
`LIUM Speaker Diarization <http://lium3.univ-lemans.fr/diarization/doku.php>`_
framework.

VoiceID can process video or audio files to identify in which slices of
time there is a person speaking (diarization); then it examines all those
segments to identify who is speaking. To do so uses a voice models
database.

To create the database you can do a "training phase" using the script ``vid``
in interactive mode, by assigning a label to the "unknown" speakers, or
you can also build yourself manually the speaker models and put in the db
using the scripts to create the gmm files.

Here an example about how use the library to create a python script to add
voices in db and to process a file to extract the speakers in it.

::

    from voiceid.sr import Voiceid
    from voiceid.db import GMMVoiceDB

    #
    #   create voice db
    #

    db = GMMVoiceDB('mydir')

    # add models to db: params the basename of 'giov_wave.wav' and the speaker,
    #  Giovanni
    db.add_model('giov_wave', 'Giovanni')
    db.add_model('fran_wave', 'Francesco')
    db.add_model('luca_wave', 'Luca')
    ...


    #
    #   extract speakers from a file
    #

    # process a video/audio file containing various speakers
    v = Voiceid(db, 'myfile.mp4')

    # extract the speakers from file and search into db
    v.extract_speakers()

    # print the clusters (one for every speaker) and relative speakers' names
    for c in v.get_clusters():
        cluster = v.get_cluster(c)
        print cluster
        cluster.print_segments()
        print


    # output

    S0 (Luca)
    00:00:42,980 to 00:00:49,140
    00:00:50,040 to 00:00:53,280
    00:00:54,150 to 00:00:59,500
    00:00:59,590 to 00:01:01,780

    S1 (Anna)
    00:01:13,010 to 00:01:17,990
    00:01:18,830 to 00:01:20,450
    00:01:20,940 to 00:01:30,300
    00:01:37,660 to 00:01:49,890
    00:01:52,510 to 00:02:00,770

    S2 (Giovanni)
    00:05:29,630 to 00:05:31,820

    S3 (Francesco)
    00:02:56,260 to 00:03:13,350
    00:03:13,350 to 00:03:33,210
    00:03:33,210 to 00:03:37,610
    00:03:37,610 to 00:03:47,340
    00:03:47,700 to 00:03:51,310
    00:03:51,600 to 00:03:53,660

"""
import os
import sys
__version__ = filter(str.isdigit, '$Rev$')


class VConf(object):
    """"Configuration for Voiceid, implemented as singleton"""
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(VConf, cls).__new__(
                                cls, *args, **kwargs)
        return cls.__instance

    def __init__(self, *args, **kwargs):
        object.__init__(self, *args, **kwargs)
        self.QUIET_MODE = False
        self.VERBOSE = False
        self.KEEP_INTERMEDIATE_FILES = False
        local = 'local'
        if sys.platform == 'win32' or sys.platform == 'darwin':
            local = ''
        try:
            import platform
            if platform and hasattr(platform,'linux_distribution') and platform.linux_distribution()[0] in ['CentOS','Fedora','Red Hat Linux','Red Hat Enterprise Linux']:
                local = ''
        except ImportError:
            pass
        self.LIUM_JAR = os.path.join(sys.prefix, local, 'share',
                                     'voiceid', 'LIUM_SpkDiarization-4.7.jar')
        self.UBM_PATH = os.path.join(sys.prefix, local, 'share',
                                     'voiceid', 'ubm.gmm')
        self.DB_DIR = os.path.join(os.path.expanduser('~'), '.voiceid',
                                    'gmm_db')
        self.GENDER_GMMS = os.path.join(sys.prefix, local, 'share',
                                        'voiceid', 'gender.gmms')
        self.SMS_GMMS = os.path.join(sys.prefix, local, 'share',
                                     'voiceid', 'sms.gmms')
        self.S_GMMS = os.path.join(sys.prefix, local, 'share',
                                   'voiceid', 's.gmms')
        self.OUTPUT_FORMAT = 'srt'          # default output format
        #self.test_path = os.path.join(os.path.expanduser('~'),
        #                                '.voiceid', 'test')
        self.output_redirect = open(os.path.devnull, 'w')
        if self.VERBOSE:
            self.output_redirect = open(sys.stdout, 'w')
