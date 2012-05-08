Abstract
========

In this paper is presented a *speaker diarization/identification system* that works *offline* (not in realtime) to identify different speakers in a video/audio track. The library and the application can be used mainly for automatic video segmentation and indexing; the audio information can be very useful to look for specific video segments (i.e. video news) where there are different speakers that speak alternatively.

The application relies heavily on the *Speaker Diarization LIUM* project, designed by the Laboratory of Computer Science University of Maine in France: it uses a type of classification *Text-independent* and extracts audio *features* in the frequency domain while the classification is carried out using *Gaussian Mixture models*. 

Our contribution was primarily to add a voice models database to the classification system, to allow the identification of the speaker only if present in the database even taken from different environments and different recording equipment, and this allow to correct errors due to a imprecise diarization, in particular when a speaker is splitted in two or more different clusters. 

The library developed is written in python with a strong object oriented design, and are also available command line and a GUI applications.

The experiments were conducted on three different datasets: the first is a set video clips from national news (TG La7), the second is a recording of voices using a microphone, and the other is a set of audio clips taken from the *VoxForge* database of english voices. 

