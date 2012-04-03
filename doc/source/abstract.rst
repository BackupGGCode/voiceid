Abstract
========

In this paper is presented a *speaker diarization/identification system*, which works *offline* to identify different speakers in a video/audio track. The application can be used mainly for automatic video segmentation and indexing; the audio information can be very useful to look for specific video segments (i.e. video news) where there are different speakers that speak alternatively.

The application relies heavily on the *Speaker Diarization LIUM* project, designed by the Laboratory of Computer Science University of Maine in France: it uses a type of classification *Text-independent* and extracts audio *features* in the frequency domain while the classification is carried out using *Gaussian Mixture models*. 

Our contribution was primarily to add a voice database to the classification system, to allow the identification of the speaker only if present in the database, and it has also allowed us to correct any errors due to a imprecise diarization.

The experiments were conducted on three different datasets: the first is a set video clips from national news (TG La7), the second is a recording of voices using a microphone, and the other is a set of audio clips taken from the *VOXFORGE* database of english voices. Tests have shown that ...

