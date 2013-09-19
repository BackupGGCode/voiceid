# -*- coding: utf-8 -*-

from distutils.core import setup
f = open('README', 'r')
long_desc = f.read()
f.close()
import sys
import os
import os.path
import subprocess


which = 'which'
if sys.platform == 'win32':
    which = 'where'

    
basedir = os.path.dirname(os.path.join(os.getcwd(), sys.argv[0]))
def my_check_output(command): 
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, 
                               stderr=subprocess.STDOUT, universal_newlines=True)
    output = process.communicate()
    retcode = process.poll()
    if retcode:
            raise subprocess.CalledProcessError(retcode, command, output=output[0])
    return output 

try:
    java_ver = my_check_output('java -version')[0].split('\n')[0]
    jv = java_ver.split(' ')[2].replace('\"', '').split('.')
    if jv[1] < 6:
        raise Exception()   
except:
    print "ERROR: java not present or wrong version  ---  >= 1.6 required"
    exit(0)

try:
    sox = my_check_output('sox --help')
except:
    print "ERROR: sox not installed"
    exit(0)
    
try:
    sphinx = my_check_output(which + ' gst-launch')
except:
    print "ERROR: GStreamer not installed"
    exit(0)

try:
    import wx
except ImportError:
    print "WARNING: Wxpython not installed: version 2.8.12 needed"

try:
    import wx.lib.agw.ultimatelistctrl as ULC
except ImportError:
    print "WARNING: Wxpython wrong version: version >=2.8.12 needed"


doc_files = []    
if sys.argv[1] == 'clean':
    my_check_output('cd doc; make clean')
elif sys.argv[1].startswith('bdist'):
    try:
        print "creating html documentation"
        my_check_output('cd doc; make html')
    except:
        print "ERROR: documentation not correctly created"
        exit(0)
    doc_dir = os.path.join(basedir, 'doc', 'build', 'en', 'html')
    doc_files = [ os.path.join(doc_dir, f) for f in os.listdir(doc_dir) if not os.path.isdir(os.path.join(doc_dir, f)) ]
    
image_dir = os.path.join(basedir, 'share', 'bitmaps')
image_files = [ os.path.join(image_dir, f) for f in os.listdir(image_dir) if not os.path.isdir(os.path.join(image_dir, f)) ]

setup(name='voiceid',
      version='0.2',
      description='Speaker recognition system',
      long_description=long_desc,
      author='Michela Fancello, Mauro Mereu',
      author_email='michela.fancello@crs4.it, mauro.mereu@crs4.it',
      url='http://code.google.com/p/voiceid/',
      platforms=['POSIX'],
      license='GNU GPL v3',
      keywords='speaker recognition asr identification Python voice audio video GMM diarization gstreamer json xmp sphinx model',
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Environment :: X11 Applications',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: POSIX',
                   'Programming Language :: Python :: 2.7',
                   'Topic :: Multimedia :: Sound/Audio :: Speech',
                   'Topic :: Software Development :: Libraries :: Python Modules', ],
      packages=['voiceid'],
      package_dir={'voiceid': os.path.join('src', 'voiceid')},
      data_files=[(os.path.join('share', 'voiceid'), [ os.path.join('share', 'LIUM_SpkDiarization-4.7.jar'), os.path.join('share', 'sms.gmms'), os.path.join('share', 's.gmms'), os.path.join('share', 'gender.gmms'), os.path.join('share', 'ubm.gmm')]),
                  (os.path.join('share', 'voiceid', 'bitmaps'), image_files),
        (os.path.join('share', 'doc', 'voiceid', 'html'), doc_files) ],
      scripts=[os.path.join('scripts', 'vid'), os.path.join('scripts', 'voiceidplayer'), os.path.join('scripts', 'onevoiceidplayer'),
               #'scripts/onevoice'
               ],
      )
