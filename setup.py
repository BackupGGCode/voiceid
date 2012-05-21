from distutils.core import setup
f = open('README','r')
long_desc = f.read()
f.close()
import sys
import os
import os.path
import subprocess

basedir = os.path.dirname(os.path.join(os.getcwd(), sys.argv[0]))
try:
    from subprocess import check_output
except ImportError:
    def check_output(command): 
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        output = process.communicate()
        retcode = process.poll()
        if retcode:
                raise subprocess.CalledProcessError(retcode, command, output=output[0])
        return output 

try:
    java_ver = check_output('java -version')[0].split('\n')[0]
    jv = java_ver.split(' ')[2].replace('\"','').split('.')
    if jv[1] < 6:
        raise Exception()   
except:
    print "ERROR: java not present or wrong version  ---  >= 1.6 required"
    exit(0)

try:
    sox = check_output('sox --help')
except:
    print "ERROR: sox not installed"
    exit(0)
    
try:
    sphinx = check_output('which sphinx_fe')
except:
    print "ERROR: CMU-sphinx not installed"
    exit(0)
    
try:
    sphinx = check_output('which gst-launch')
except:
    print "ERROR: GStreamer not installed"
    exit(0)

try:
    import wx
except ImportError:
    print "ERROR: Wxpython not installed: version 2.8.12 needed"
    exit(0)

try:
    import wx.lib.agw.ultimatelistctrl as ULC
except ImportError:
    print "ERROR: Wxpython not updated: version 2.8.12 needed"
    exit(0)


doc_files = []    
if sys.argv[1] == 'clean':
    check_output('cd doc; make clean')
elif sys.argv[1].startswith('bdist'):
    try:
        print "creating html documentation"
        check_output('cd doc; make html')
    except:
        print "ERROR: documentation not correctly created"
        exit(0)
    doc_dir = os.path.join(basedir, 'doc/build/html')
    doc_files = [ os.path.join(doc_dir, f) for f in os.listdir(doc_dir) if not os.path.isdir( os.path.join(doc_dir, f) ) ]
    
image_dir = os.path.join(basedir, 'share/bitmaps')
image_files = [ os.path.join(image_dir, f) for f in os.listdir(image_dir) if not os.path.isdir( os.path.join(image_dir, f) ) ]

setup(name='voiceid',
      version='0.1',
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
                   'Programming Language :: Python :: 2.6',
                   'Topic :: Multimedia :: Sound/Audio :: Speech',
                   'Topic :: Software Development :: Libraries :: Python Modules',],
      packages=['voiceid'],
      package_dir={'voiceid': 'src/voiceid'},
      data_files=[('share/voiceid', ['share/LIUM_SpkDiarization-4.7.jar', 'share/sms.gmms', 'share/gender.gmms','share/ubm.gmm']), 
                  ('share/voiceid/bitmaps', image_files ),
		('share/doc/voiceid/html', doc_files )],
      scripts=['scripts/vid', 'scripts/voiceidplayer', 'scripts/onevoiceidplayer', 
               #'scripts/onevoice'
               ],
      )
