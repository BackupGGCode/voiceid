

# FAQ #

## Differents among Speaker Recognition, Speech Recognition and so on? ##
_Speaker diarization_: audio segmentation according to the different speaker's voices.

_Gender recognition_: gender identification of a voice (male, female).

_Speaker recognition_:
  * speaker verification: identity verification: is he Marcus? yes/no. Can be text dependent (by password) or text indipendent (regardless of what is saying).
  * speaker identification: name identification from a speakers database (who is speaking?)
_Speech to text or speech recognition_: speech transcription

## What is Voiceid? ##
Voiceid is a library/system (written in Python) that identifies the various voices within a audio track (diarization) and associate them a name if present in the database (identification), also according to the gender.

## Why Python and not Java? ##
The core of Voiceid ([LIUM\_SpkrDiarization](http://lium3.univ-lemans.fr/diarization/doku.php/welcome) lib) is written in Java, and at the beginning Voiceid was a set of shell scripts running LIUM tasks. We switch to Python when it become more complex. We are planning to switch to Java in order to simplify the access to LIUM routines and for better performances.

## How can I use it? ##
Voiceid is a library, so you can write python programs using it, just look at the [wiki](UsingLibrary.md) and at the [API](API.md)(check if up to date). You can also use some scripts that are included, in particular `vid`, that do all the recognition work.

## Has Voiceid a GUI interface? ##
Yes, there is a GUI interface named `voiceidplayer` that allows to do all the things that can do `vid` and shows all elaboration progress and results in a simple window.

## What Voiceid takes in input? ##
Voiceid takes in input WAVE or video files that can be read by GStreamer. It convert the audio track to a WAVE file having these specs "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz".

## What Voiceid returns in output? ##
The format of the output file can be: srt, [json](http://en.wikipedia.org/wiki/JSON) or [XMP](http://www.adobe.com/products/xmp/). Each of these contains the time intervals in which each speaker speaks into the video. Srt ([SubRip](http://en.wikipedia.org/wiki/SubRip#SubRip_text_file_format)) is a file format used generally for video subtitles.

## Does Voiceid work in real time? ##
No, it doesn't work in real time.

## What kind of video file can be accepted in voiceidplayer gui? ##
The video formats accepted are those of [mplayer](http://www.mplayerhq.hu/design7/info.html).

## In which OS can run Voiceid? ##
It works well on Linux, Windows, Mac OS X (tested on Ubuntu 12.04, Debian 6.0, Windows7).

## I tried to run Voiceid on Ubuntu 12.04/12.10 but i can not produce the '. i.seg'. What is the problem? ##
This problem is relative to the sphinx\_fe output (a .mfcc file), because the sphinxbase-tools package installable in ubuntu 12.04 (sphinxbase-utils 0.4.1-0ubuntu4 notice the trailing 4) doesn't work properly.
You have to remove the package by apt-get and install an older package (sphinxbase-utils 0.4.1-0ubuntu1, trailing 1) that you can find here,
https://launchpad.net/ubuntu/karmic/i386/sphinxbase-utils/0.4.1-0ubuntu1 (direct link to the deb http://launchpadlibrarian.net/30727966/sphinxbase-utils_0.4.1-0ubuntu1_i386.deb).
**Ensure you have installed the right version by typing `dpkg -s sphinxbase-utils`.**
You must have a similar output:
  * Package: sphinxbase-utils
  * Status: install ok installed
  * Priority: optional
  * Section: sound
  * Installed-Size: 196
  * Maintainer: Ubuntu MOTU Developers <ubuntu-motu@lists.ubuntu.com>
  * Architecture: i386
  * Source: sphinxbase
  * Version: 0.4.1-0ubuntu1
  * Depends: libasound2 (>> 1.0.18), libc6 (>= 2.7), libsphinxbase1 (>= 0.4.1), perl


## How can i use voiceid for the fastest gender detection only? ##
To do gender detection you have to write a python script. You have to
use Voiceid in "single mode", passing a parameter single=True when you
instantiate the Voiceid object. It assumes the wave has only one
speaker.

Here a little snippet of code to do that:
```
from voiceid.db import GMMVoiceDB
from voiceid.sr import Voiceid
import os
v = Voiceid(GMMVoiceDB(os.path.expanduser("~/.voiceid/gmm_db")), "sample-8kHz.wav", single=True)
v.extract_speakers()
print v.get_clusters()['S0'].get_gender()  # when in single mode the cluster (only one in this mode) has label 'S0'
```
If you have more speakers you can use Voiceid as described in the wiki.

You could also use the row `fm._gender_detection(filename)` function,
but in this case it's up to you to convert the wave in input and to
read from a .seg file the output.

## Can I do some tweaking to the male and female thresholds? ##

To tune up the way gender is detected you have to look at
`fm._gender_detection(filename)`, where are called two routines of
LIUM\_SpkrDiarization that do that.
The routines just compute, after a segmentation, a score by matching
with a model of male and female voices (once installed the model file
should be /usr/local/share/voiceid/gender.gmms).
To tune the threshold you have to look at the LIUM implementation of
MScore, otherwise you could build a new model for gender, but we didn't make a new model, we
use the one in the LIUM package.

## How to clean the voice db and work with an empty voice db? ##

Just remove all files in `~/.voiceid/gmm_db/{F,M,U}` .

## What are the technical reasons Voiceid does not run in real-time? Is it conceivable that voiceid could run in real-time? ##

Voiceid does not work in real-time mainly because LIUM does not work in real-time (for what I know). The scripts onevoice and onevoiceidplayer simulate a real-time behavior by working on segments of time (while recording the next segment) but to achieve a good recognition you have to take at least 10 seconds of voice. Then you have to work on that data and if you have a fast processing hardware you could anyway check in a database of hundred of models (according to your goal), and this operation may take a lot of time.