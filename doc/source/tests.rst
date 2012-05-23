﻿Tests
=======
Three Datasets were used for testing: the first was built using audio tracks from italian news broadcast (105 speakers), the second was a set of audio files taken from the VoxForge [#]_ collection and the last was a set of ad hoc recordings with a consumer microphone.

In the first case we take audio segments of variable length of the speakers in the examined *video news*: the *training set* has 43 female and 62 male speaker voices.

The second dataset was the product of a crowdsourcing from VoxForge, a set of voices recorded by a community of volunteers, all in english. The voices dataset was splitted in two sets, half in the *training set* and the other half in the *test set*. The use of samples of different size can show how well the system works according to the dimension of the wave files and how long must be the wave track to have a good answer.

In the third case, to better examine the system perfomances, we built an ad hoc training set, recording 34 voices with a normal consumer microphone, 22 male and 12 female, of about 30 seconds each, for about 17 minutes total.


First test
----------
The first tests run are focused on evaluating the predictive capabilities of the system, verify its reliability and if possible improve it using some strategies. Using part of the speech corpus of Voxforge we built a training set of 624 GMM, one model for each speaker; the test was performed using 2598 MFCC relative to 162 speakers as test set.

.. figure::  /img-latex/db_testset.png
 :align: center


The samples used in this test have different length, quality and dimensions; this hardly reduces the performances but in this way we can analize the system with a "random" input and see which parameter is more affective.

Each MFCC was compared with each GMM in the db, producing a set of scores useful to evaluate the goodness of the classifier answer. We can see in the following table that False Positive are almost as much as True Positive. After a brief analysis of data we notice that the average distance from first and second most probable speaker scores, in case of true positive, was about 0.07, when in false positive cases was 0.02. According to this we added a filter that reject cases where the distance is less then 0.07.

.. figure::  /img-latex/tabella-soglia.png
 :align: center

 Threshold


The table shows the number of true positives (correct recognition), true negatives (not recognized), false positives (false alarms), false negatives (wrongly not recognized) in case we use or not the threshold to determine if the classification is reliable. This threshold does not influence the true positives but allow the 97% of false positives to set correctly into the true negatives category, strongly decreasing the false alarm count.

Analyzing the samples' length is also visible that the system works in an effective way as the length grows.

.. figure::  /img-latex/confronti_l_wave_en.png
 :align:   center

 Over five seconds is clear that most of the classification are correct.
	 
.. figure::  /img-latex/resume_table.png
 :align:   center

 The test results.

   +----------------------------------------------+
   |   Legend                                     |
   +===+==========================================+
   | A |Just best score                           |
   +---+------------------------------------------+
   | B |Best score with distance threshold (0.07) |
   +---+------------------------------------------+
   | C |Just waves bigger than 5 seconds          |
   +---+------------------------------------------+
   | D |Just waves bigger than 8 seconds          |
   +---+------------------------------------------+
   | E |Just waves bigger than 10 seconds         |
   +---+------------------------------------------+


Another useful indicator to examine the answer's goodness is **Sensitivity**; it checks the capacity of the system to correctly classify the speakers, and it is represented in the following formula:

.. figure::  /img-latex/sensitivity.png
 :align:   center

In our case, because all is relative to a percentage, the sensitivity value is the same as the recognized percentage. We can see that we reach the max sensitivity in segments bigger than 8 seconds (sensitivity of 0.83).


Second test
------------
To evaluate the segmentation/diarization and the association of the cluster to a db speaker was used the voice database build from an italian broadcast news, about 100 voices extracted from 10 different editions of the show. The *test set* was build from 3 more broadcast news videos of about 30min each. To analyze the diarization we proceed in this way: we run the automatic diarization/identification process and compare the results to the diarization/identification process in interactive mode (with user feedback, only for the identification task, not for the segmentation).

.. figure::  /img-latex/test_tg7.png
 :align:   center

 TgLa7 test results.
	
   +------------------------------------------------------------------------------------------------------------------------+
   |   Legend                                                                                                               |
   +===+====================================================================================================================+
   |A_A|speaker in the db and correctly recognized                                                                          |
   +---+--------------------------------------------------------------------------------------------------------------------+
   |U_U|speaker correctly identified as unknown, not in the db and without identity information (es. pedestrians interviews)|
   +---+--------------------------------------------------------------------------------------------------------------------+
   |U_N| speaker not in the db (new name added in interactive mode) and correctly defined unknow                            |
   +---+--------------------------------------------------------------------------------------------------------------------+
   |U_A| speaker in the db but wrongly defined unknown                                                                      |
   +---+--------------------------------------------------------------------------------------------------------------------+
   |A_B| speaker in the db but wrongly identified as another speaker                                                        |
   +---+--------------------------------------------------------------------------------------------------------------------+
   |A_U| speaker wrongly identified as known but without identity information (see U_U)                                     |
   +---+--------------------------------------------------------------------------------------------------------------------+

As shown in the table, the test give us good results, more in deep we see that there are six cases for every speaker (cluster) recognized by the diarization phase. Three cases are good and three are bad. Naturally the best case is when the speaker is correctly recognized (A_A); obviously the situation is more complicated, you can have new speakers that you want to add to the db (U_N), and you can have new speakers that you do not know the name and then you can't (don't want to) put them in the db (U_U). These are the good cases, even if the best case is when the system gives a name to the voice, but you always can find a speaker not in the db (if you haven't a limited number of speakers in the videos/audios), but in these cases the system work is correct. When otherwise a speaker "unknown" is labeled as a speaker already in the db (U_A) or a speaker already present in the db is recognized as another (A_B), or when a speaker in the db is labeled as unknown (A_U), these are the bad cases. To reduce this effect you can, in interactive mode (command line utility), correct manually the speakers labels/names and it automatically update the speaker model in the db building a new model from the wave processed.


Third test
----------
The *training sets* are composed of GMM files, one for each speaker, the *test sets* are composed of MFCC feature files.
To optimize the search of the best speaker the voice db is splitted for gender in three different directories, F (female), M (male), U (not recognized).

.. figure::  /img-latex/confronto-thread-time-tabella2.png
 :align:   center

 Summary table.

.. figure::  /img-latex/confronto-thread-time-12.png
 :align:   center

 12 matching-score compared to the thread's number.

.. figure::  /img-latex/confronto-thread-time.png
 :align:   center

 22 matching-score compared to the thread's number.

The aim of the last tests is to analyze the performances of the system in multithreading on a multiprocessor platform.
Graphs in figure show the average response times obtained running differents voice matching using one MFCC and different GMM models in the ad hoc db. Best performances on a 8 cpus are about half a second for every GMM. Correctly the performances increase according to the number of threads but the speedup is not really impressive. In particular we can see that when the number of threads is about the number of cpus we have almost the best performances, so it is not useful to use more threads then the cpus.
By the way it's also important to tell that all the samples used for this test were correctly recognized by the system.

.. [#] VoxForge was build up to gather audio transcriptions for model building in speech recognition systems like ISIP, HTK, Julius and Sphinx. The aim of this project is to make available with open licenses *Speech Corpus* of different languages, and speech models for as many languages is possible.
