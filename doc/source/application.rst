Application
============

To improve the usability of the system was designed a simple interface with an output light.

.. figure::  /img-latex/player1.png
   :align:  center

As you can see from above, the application has been made using a player that makes it possible to see in the video the speakers detected by automatic detection. Once loaded the video we can to start the extraction of the speakers that will later be displayed on the right of the player. At this point you can, using the checkboxes, select the speakers of interest: slider below the player will display the selected intervals in which each speaker speaks, distinguished by a different color assigned to each of them.

.. figure::  /img-latex/intervalli_speakers.png
   :align:  center

As described above, each cluster in the diarization output is compared with previous models saved in a database: the application allows you to select the database and start the recognition  process.  If speakers in database folder are not compatible with the items extracted, their clusters will appear with the label *unknown*: to train the system by adding these items *unknown* to the database, simply click on the relevant line in the list and edit the correct name.

.. figure::  /img-latex/player2.png
    :align:  center

All data can be saved using the higher toolbar, in *json* format: this allows you to directly load a video and view the information you previously extracted.
