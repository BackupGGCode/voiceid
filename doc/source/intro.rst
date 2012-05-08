Introduction
============

Today the extraction of information from multimedia content has become a target of a wide circle of national scientific community.
Only recently the audio has become an additional source of information for content analysis because it allows a better classification of the media.
A system able to process a video using its audio allows you to find all the segments in which the different speakers speak even if not visible; the few existing open-source systems that use a voices database, do not handle the case when the input voice does not belong to any previously recorded speaker.
 
*Speaker Identification* System proposed aim to satisfy the needs described above: associate to a set of items as input, a group of known voices (speakers) that are more similar. The video segmentation task is done by the *Diarization* system in the project LIUM [#]_ that is able to partition an input audio stream into homogeneous segments based on the identity of the speakers. *LIUM SpkDiarization* includes a complete set of tools to build a speaker identification system, from the audio signal to speaker clustering. These tools include extraction of features with the MFCC calculation, silence detection and classification using *Gaussian Mixture Models*.
Joining a voice database with the classification system you can then study the behavior based on the scores obtained by any voice with voice models. To accept or reject a speaker identity is necessary to identify a decision threshold relative to the scores. 
At the same time, the decision threshold may be too restrictive and it is necessary to check some other factors, like distance from second and so on.
Another objective is to reduce the response time of the system and thus allow a faster recognition using the information on the gender of the speakers speakers or building a database of individual models for each user entry previously recorded.

The first section will describe in an essential way the system architecture and in more detail the individual macro-blocks. In the second chapter will be described in a comprehensive manner the tests run and at the end a description of the Voiceid application. In appendix the library API.

For the algorithms used in the diarization and recognition tasks you can take a look to the official LIUM SpkrDiarization project page (http://lium3.univ-lemans.fr/diarization/doku.php).

.. [#] It is a project started in 2007 in the Laboratory of Computer Science University of Maine (France).
