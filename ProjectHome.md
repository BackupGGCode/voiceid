A _speaker recognition/identification_ system written in Python, based on the [LIUM Speaker Diarization](http://lium3.univ-lemans.fr/diarization/doku.php) framework.

**VoiceID** can process video or audio files to identify in which slices of time there is a **person speaking** (_diarization_); then it examines all those segments to identify _who is speaking_. To do so you must have a **voice models database**. To create the database you have to do a "train phase", in _interactive mode_, by assigning a label to the unknown speakers.

You can also build yourself the speaker models and put those in the db using the scripts to create the gmm files.
It can run on Windows, Linux, Mac OS X.
You can find a code example about the underling python library in the wiki page [UsingLibrary](http://code.google.com/p/voiceid/wiki/UsingLibrary).

In the [FAQ](http://code.google.com/p/voiceid/wiki/FAQ) section you can find answers to general questions.


<a href='https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=mauromereu%40gmail%2ecom&lc=IT&item_name=voiceid&no_note=0&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_SM%2egif%3aNonHostedGuest'><img src='https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif' /></a>

---

Dependencies:
  1. `Python 2.7`
  1. `Java >= 1.6`
  1. `GStreamer (base, good, bad, tools)`
  1. `SoX`

For the GUI:
  1. `wxPython >= 2.8`
  1. `mplayer`
  1. `MplayerCtrl`

Tested on Ubuntu 12.04/12.10

> ![http://voiceid.googlecode.com/svn/trunk/doc/source/img-latex/icon-new-black-64x64_viola.png](http://voiceid.googlecode.com/svn/trunk/doc/source/img-latex/icon-new-black-64x64_viola.png)  Available Voiceid version 0.3 for [download](http://code.google.com/p/voiceid/downloads/list)

> [Installation instructions for Windows7](http://code.google.com/p/voiceid/wiki/Windows_Setup)



Setup in Ubuntu:

```
  $ sudo apt-get install python2.7 python-wxgtk2.8 openjdk-7-jdk gstreamer0.10-plugins-base \
      gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gstreamer0.10-plugins-ugly \
      gstreamer-tools sox mplayer python-setuptools
  $ sudo easy_install MplayerCtrl
  $ svn checkout http://voiceid.googlecode.com/svn/trunk voiceid
  $ cd voiceid
  $ sudo python setup.py install

```
Usage:
> to analyze a video/audio file in interactive mode (the system ask you who is speaking if not yet present in db) just type (if you have /usr/local/bin in your path):
> > `vid -i INPUT_FILE -u`


> to analyze a video/audio file in batch mode
> > `vid -i INPUT_FILE`



> to build a voice model from a given wav file
> > `vid -s SPEAKER_ID -g INPUT_FILE`



> to analyze a video/audio file in interactive mode, writing the output in json file
> > `vid -i INPUT_FILE -f json -u`


> to analyze a noisy audio file in interactive mode, writing the output in json file
> > `vid -i INPUT_FILE -f json -n -u`


> to see other options
> > `vid -h`

Output:

> the output of the current svn release is available as json file, srt file and an experimental xmp sidecar file format

GUI:
> `voiceidplayer`

> to run voiceidplayer with a video/audio file and database path
> > `voiceidplayer video_file database_path`

![http://voiceid.googlecode.com/svn/trunk/doc/source/img-latex/player1_pix.png](http://voiceid.googlecode.com/svn/trunk/doc/source/img-latex/player1_pix.png)