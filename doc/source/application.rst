Applications
============

When Voiceid is installed in your system, you will find some useful applications that can be used to extract information from your audios or videos, to build voice models and to do speaker indentification.

vid
----
The main application is the command line utility ``vid``. It can execute the extraction of the speaker info from audio and video files, also in interactive mode (with user feedback), and can generate sidecar files in three formats: json, xml (xmp) or srt (subtitle files where the speakers names are shown as subs).
It can also generate voice models from audio files.

Use examples:

::

    speaker identification
    
        vid [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -i INPUT_FILE
    
        user interactive mode

        vid [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -i INPUT_FILE -u    

    speaker model creation

        vid [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g INPUT_FILE

        vid [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g WAVE WAVE ... WAVE  MERGED_WAVES 

Option flags:

::

  -h, --help            show this help message and exit
  -v, --verbose         verbose mode
  -q, --quiet           suppress prints
  -k, --keep-intermediatefiles
                        keep all the intermediate files
  -i FILE, --identify=FILE
                        identify speakers in video or audio file
  -g, --gmm             build speaker model
  -s SPEAKERID, --speaker=SPEAKERID
                        speaker identifier for model building
  -d PATH, --db=PATH    set the speakers models db path (default:
                        /home/mauro/.voiceid/gmm_db)
  -j PATH, --jar=PATH   set the LIUM_SpkDiarization jar path (default:
                        /usr/local/share/voiceid/LIUM_SpkDiarization-4.7.jar)
  -b PATH, --ubm=PATH   set the gmm UBM model path (default:
                        /usr/local/share/voiceid/ubm.gmm)
  -u, --user-interactive
                        User interactive training
  -f OUTPUT_FORMAT, --output-format=OUTPUT_FORMAT
                        output file format [ srt | json | xmp ] (default srt)


voiceidplayer
--------------
To improve the usability of the system it's possible to use a simple GUI (``voiceidplayer``) with a better output visualization.

.. figure::  /img-latex/player1.png
   :align:  center

As you can see from above, the application has been made using a player that makes it possible to see in the video the speakers automatically detected. Once loaded the video we can start the extraction of the speakers that will later be displayed on the right of the video. At this point you can select the speakers of interest using the checkboxes: the slider below the video will display the selected intervals in which each speaker speaks, distinguished by a different color.

.. figure::  /img-latex/intervalli_speakers.png
   :align:  center

As described above, each cluster in the diarization output is compared with previous models saved in a database: the application allows you to select the database and start the recognition process. If the speakers extracted are not recognized as voices in the database, their clusters will appear with the label *unknown*: to train the system by adding these *unknown* voices to the database, simply click on the relative line in the list and edit the name.

.. figure::  /img-latex/player2.png
    :align:  center

All data can be saved in *json* format using the menu on top: this allows also to directly load a video and view the information previously extracted. More in deep, if you load a video and you have a "sidecar" file with the same name of the video, but with extension ".json", if in right format it will be analyzed as a "dump" of the information extracted by a previous run of the speaker recognition, showing all the relative results.


onevoiceidplayer
-----------------
This application allow the users to record a voice to build a model, and to try to recognize a live voice in the database. It has a simple GUI, but it's just a prototype for tests.