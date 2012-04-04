Processing flow
﻿===================

In this section are described by diagrams the various stages that make the whole process of classification and identification of the *speaker*. First ​​a brief description of the capture of audio or video data input and the diarization process, then the creation of the database of GMM models and the process of *matching score* between MFCC and GMM for recognition of a probable *speaker*. 

Diarization
--------------

The system handles audio and video files; in case the input is a video file or compressed audio, **GStreamer** is used to extract a audio track as WAVE file, RIFF little-endian data, Microsoft PCM, 16 bit, mono 16000 Hz.

The *LiumSpkrDiarization* tool can segment the audio track and the output is cleaned from non spoken segments by the *silence detector*; more in deep the diarization produces a **seg** file, where are listed all the time intervals labeled with the same label (S0, S1, ... , Sn) that identify the same voice, and a char (F, M, U) for the gender.
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

The system database is composed of the GMM models files organized by gender in three folders: F (female), M (male), U (not recognized). Every GMM file can be extended with different models of the same speaker: that is really useful because the system does not impose constraints about the way the audio is recorded; with just one model for every speaker it's possible that in some cases the speaker is not recognized when speaking in different environments and with different recording equipments. Different models allow more probabilities to recognized the speaker for a wide samples sets.

To build the gmm model it is used the MFCC with the *features* and the *seg* file of the original wave of the voice.

.. figure::  /img-latex/build_gmm.png
   :align:   center
   
   The GMM model processing and db add according to the gender.


Speaker recognition
-------------------------

La parte più interessante del sistema è quella relativa al riconoscimento dello speaker sulla base delle voci presenti nel database; naturalmente deve poter prevedere anche il caso in cui chi parla sia “sconosciuto” . Ogni nuova voce viene analizzata sulla base del relativo MFCC che verrà quindi confrontato con tutti i GMM presenti nel db utilizzando l'**MScore** di *Lium*: più precisamente il metodo **MScore** della libreria prende in input un file MFCC di feature audio e un file contenente uno o più modelli GMM e calcola uno score generalmente negativo, che può andare da circa -31 a circa -34, che è tanto migliore quanto è maggiore (si avvicina di più verso 0).

.. figure::  /img-latex/Mscore2.png
   :align:   center

   Un MFCC viene confrontato con n GMM attraverso l'MScore producendo una serie di scores; il maggiore di essi sarà considerata lo score migliore.

Per ottimizzare i tempi di processazione è possibile generare una serie di thread che in concorrenza si dividono i confronti da fare tra i file GMM del database e i file MFCC dei singoli cluster; la scelta di mantenere distinti i modelli vocali dei differenti *speakers* nasce anche da questa esigenza. 

Una volta ottenuto il nome dello speaker con lo score più alto (*best score*) è necessario verificare se il risultato è attendibile: per prima cosa bisogna accertarsi che lo score sia “sufficientemente” alto per poter escludere la possibilità che lo speaker non sia presente nel database. Per fare questo è stato individuata una soglia in modo empirico, convergendo alla fine sul valore -33: se il *best score* risulta essere minore di tale soglia, ciò indica che probabilmente lo speaker ricercato non è presente nel database. In caso contrario verrà effettuato un altro controllo per accertare che il *best score* sia “sufficientemente” indicativo ovvero che la distanza dal secondo score classificato sia maggiore di una certa quantità: tale valore è stato ottenuto mediante differenti tests, portando a ritenere accettabile una distanza non minore a 0,07.
Nel caso in cui la distanza tra il primo e il secondo risultasse minore, si ritiene inattendibile il risultato, pertanto la voce viene considerata sconosciuta, in caso contrario alla voce verrà assegnato  lo speaker che ha prodotto il *best score* .

.. figure::  /img-latex/best_speaker.png
   :align:   center

   Una volta ottenuto il *best score*,  verrà verificata l'attendibilità del potenziale riconoscimento.


.. [#] Sphinx-4 è un sistema di riconoscimento vocale scritto interamentenel linguaggio di programmazione JavaTM. E' stato creato attraverso una collaborazione tra il gruppo Sfinge presso la Carnegie Mellon University, SunMicrosystems Laboratories, Mitsubishi Electric Research Labs (MERL), e HewlettPackard (HP), con il contributo dell'Università della California a Santa Cruz (UCSC) e il Massachusetts Institute of Technology (MIT).

