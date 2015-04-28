# Installation instructions for Windows #

> ## Base dependencies ##
  * [Python 2.7](http://www.python.org/getit/)
  * Java 1.7
  * [Sox](http://sourceforge.net/projects/sox/files/latest/download?source=files)
  * GStreamer (ex. [GStreamer-WinBuilds](http://code.google.com/p/ossbuild/downloads/detail?name=GStreamer-WinBuilds-LGPL-x86-Beta04-0.10.7.msi&can=2&q=))
  * [Vlc](http://www.videolan.org/vlc/)

> ## GUI dependencies ##
  * wxPython 2.8.12 (ex. [wxPython2.8-win32-unicode-2.8.12.1-py27 ](http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/wxPython2.8-win32-unicode-2.8.12.1-py27.exe/download?use_mirror=garr))
  * Mplayer 0.6.9 (ex. [smplayer-0.6.9-win32](http://sourceforge.net/projects/smplayer/files/SMPlayer/0.6.9/smplayer-0.6.9-win32.exe/download))
  * [MplayerCtrl-0.3.3](http://pypi.python.org/packages/any/M/MplayerCtrl/MplayerCtrl-0.3.3.linux-i686.exe#md5=c5eafb16e5ab4c2517a9568e2bbd9fe4)

**All dependencies should be [included](http://searchsystemschannel.techtarget.com/feature/Setting-Windows-7-environment-variables) in the system path.**


## Installation ##

Install the software dependencies above.

Download the package (or checkout the source) and extract it.

Open the windows terminal **cmd** and go to the extracted dir (ex. `C:\Users\myuser> cd voiceid-0.1` ).

Then just run

`C:\Users\myuser\voiceid-0.1> python setup.py install`

Add voiceid directory to pythonpath.

From the same dir you should be able to run

`C:\Users\myuser\voiceid-0.1> python scripts/vid -h`

to ensure everything works well.