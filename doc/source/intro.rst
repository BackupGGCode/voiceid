Introduction
============

Today the extraction of information from multimedia content has become a target of a wide circle of national scientific community. 
Only recently the audio has become an additional source of information for content analysis because it allows a better classification of the media. 
A system able to process a video using its audio allows you to find all the segments in which the different speakers speak even if not visible; the few existing open-source systems  that use a voices database, do not handle the case when the input voice does not belong to any previously recorded speaker.
 
*Speaker Identification* System proposed aim to satisfy the needs described above: associate to a set of items as input, a group of known voices (speakers) that are more similar. The video segmentation task is done by the *Diarization* system in the project LIUM [#] _ that is able to partition an input audio stream into homogeneous segments based on the identity of the speakers. *LIUM SpkDiarization* includes a complete set of tools to build a speaker identification system, from the audio signal to speaker clustering. These tools include extraction of features with the MFCC calculation, silence detection and classification using *Gaussian Mixture Models*. 
Joining a voice database with the classification system you can then study the behavior based on the scores obtained. To accept or reject a speaker identity is necessary to identify a decision threshold. 
At the same time, the decision threshold may be too restrictive and it is necessary to check some other factors. 
Another objective is to reduce the response time of the system and thus allow a faster recognition using the information on the gender of the speakers speakers or building a database of individual models for each user entry previously recorded. 

The first section will describe in an essential way the system architecture and in more detail the individual macro-blocks. In the second paragraph will be described in a comprehensive manner the characteristics of the database will be listed in the third stage of testing, at the end a description of the Voiceid application and in appendix the library API.

.. [#] It is a project started in 2007 in the Laboratory of Computer Science University of Maine (France).
