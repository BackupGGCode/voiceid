Processing Flow
===============
In this section are described by diagrams the various stages that make the whole process of classification and identification of the speaker. Starting with a short description of the capture of audio or video data input and the diarization process, then the creation of the database of GMM models and the process of *matching score* between MFCC and GMM for recognition of a probable *speaker*. 

Diarization
--------------

The system handles audio and video files; in case the input is a video file or compressed audio, **GStreamer** is used to extract a audio track as WAVE file, RIFF little-endian data, Microsoft PCM, 16 bit, mono 16000 Hz.

The *LiumSpkrDiarization* tool output and inputs, except for the audio files, are generally text files, which are mapped directly into the objects of the library to hidden  to the programmers.  The *LiumSpkrDiarization* tool can segment the audio track and the output is cleaned from non spoken segments by the *silence detector*; more in deep the diarization produces a **seg** file, where are listed all the time intervals labeled with the same label (S0, S1, ... , Sn) that identify the same voice, and a char (F, M, U) for the gender.
As can be seen in the following example taken from a *seg* file, the diarization process gives also information about audio quality (S = studio, T = telephone). For each segment is also specified the start time and the duration.

	cluster:S0

		Enrico_Mentana_a_Invasioni_Barbariche 1 0 435 F S U S0

		Enrico_Mentana_a_Invasioni_Barbariche 1 507 207 F S U S0

	cluster:S10

		Enrico_Mentana_a_Invasioni_Barbariche 1 714 1076 F S U S10
		
		Enrico_Mentana_a_Invasioni_Barbariche 1 3154 444 F S U S10
			
		Enrico_Mentana_a_Invasioni_Barbariche 1 3598 431 F S U S10
	
	cluster:S102	
	
		Enrico_Mentana_a_Invasioni_Barbariche 1 4836 163 F S U S102
	
		Enrico_Mentana_a_Invasioni_Barbariche 1 30977 260 F S U S102
	
		Enrico_Mentana_a_Invasioni_Barbariche 1 49615 219 F S U S102

	…

Having the **seg** file we tried to identify the speakers found in the diarization process, cutting the original wave in several waves, one for each segment.
With this audio slices for each speaker, we extract the *MFCC* audio features using *Sphinx* [#]_.


.. figure::  /img-latex/diar_mfcc.png
   :align:  center

   In the diagram above the data acquisition and diarization processing.

Database
-----------

The system database is composed of the GMM models files organized by gender in three folders: F (female), M (male), U (not recognized). Every GMM file can be extended with different models of the same speaker: thit is really useful because the system does not impose constraints about the way the audio is recorded; with just one model for every speaker it's possible that in some cases the speaker is not recognized when speaking in different environments and with different recording equipments. Different models allow more probabilities to recognize the speaker for a wide samples sets.

To build the gmm model it is used the MFCC with the *features* and the *seg* file of the original wave of the voice.

.. figure::  /img-latex/build_gmm.png
   :align:   center
   
   The GMM model processing and db add according to the gender.


Speaker recognition
-------------------------

The core of the system is the speaker recognition using a database mapped voices; must be also recognized the case when who speaks is "unknown". Every new voice MFCC is analyzed, compared against all GMM in the db using the *Lium* **MScore**: more in deep the **MScore** method takes in input the feature audio MFCC file and a file containing one or more GMM models and compute a score, usually negative, that goes from about -31 to -34, where bigger is better (closer to zero).


.. figure::  /img-latex/Mscore2.png
   :align:   center

   A MFCC file is compared with n GMM files using MScore giving a set of scores; the bigger is considered as the best.

To optimize the processing it is possible to generate a set of threads that concurrently share the comparisions among GMM files in the db and MFCC of the clusters; the choice to keep in different files the voice models of different *speakers* is also for this purpose.   

Once obtained the name of the speaker having the *best score* it is necessary to verify if the result is reliable or not: first of all must be sure that the score is sufficiently high to limit the possibility that the speaker is not present in the db. To do that has been identified an empirical threshold, with a value of -33: if the *best score* is lower than this threshold, it means that the speaker probably is not present in the db. Otherwise another check is performed to be more confident that the *best score* is indicative "enough", that is that the distance from the *second classified* score is higher than a given value: the value obtained by some empirical tests is a distance not less then 0.07.  
In case the distance between the first and the second is lower then this value, the result is taken as unreliable, that is the speaker is considered unknown (not in the voice db).

.. figure::  /img-latex/best_speaker.png
   :align:   center

   Once obtained the best score, is verified the reliability of the recognition.


   
.. [#] Sphinx-4 is a speech/speaker recognition system in Java. It is build in collaboration among the Sphinx group at Carnegie Mellon University, SunMicrosystems Laboratories, Mitsubishi Electric Research Labs (MERL), HewlettPackard (HP), the University of California in Santa Cruz (UCSC) and the Massachusetts Institute of Technology (MIT).

