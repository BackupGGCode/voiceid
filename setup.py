from distutils.core import setup
f = open('README','r')
long_desc = f.read()
f.close()
import os
import os.path
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
      data_files=[('share/voiceid', ['share/LIUM_SpkDiarization-4.7.jar',
'share/sms.gmms', 'share/gender.gmms',
'share/ubm.gmm']), ('share/voiceid/bitmaps', [ os.path.join('share/bitmaps', f) for f in os.listdir('share/bitmaps') if not os.path.isdir( os.path.join('share/bitmaps', f) ) ] )],
      scripts=['scripts/vid', 'scripts/voiceidplayer', 'scripts/onevoiceidplayer', 
               #'scripts/onevoice'
               ],
      )
