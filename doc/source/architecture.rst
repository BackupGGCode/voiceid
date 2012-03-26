Flusso di elaborazione
===================
 
In questa sezione si vuole provare a descrivere con l'utilizzo di diagrammi, i vari stadi che costituiscono l'intero processo di classificazione e identificazione dello *speaker*. Inizialmente viene fatta una breve descrizione dell' acquisizione del dato audio o video in input e la sua successiva elaborazione tramite diarization, di seguito la creazione del database attraverso i modelli GMM e il conseguente processo di *matching score* tra MFCC e GMM per il riconoscimento o meno di un eventuale *speaker*.

Diarization
--------------

Il sistema supporta in input sia tracce audio che video; nel caso di un flusso video in ingresso ,verrà estratto l'audio attraverso l'utilizzo della libreria GStreamer sulla base delle seguenti caratteristiche: WAVE file, RIFF little-endian data, Microsoft PCM, 16 bit, mono 16000 Hz.
Tramite il tool *LiumSpkrDiarization*  è possibile effettuare la segmentazione della traccia audio ripulita attraverso il *silence detector* di eventuali pause nel parlato; più precisamente la diarization restituisce un file seg in cui vengono elencati degli intervalli temporali etichettati attraverso una stessa label (S0, S1..Sn) ad indicare la medesima voce ed, una lettera (F, M, U) ad indicare il genere.
Una volta ottenuto il file **seg** abbiamo cercato di identificare i singoli speaker individuati dalla segmentazione, tagliando l'wave originale in singoli wave, uno per ogni segmento. 
Una volta ottenuti i differenti spezzoni audio per ogni speaker, si è potuto procedere con l'estrazione delle *features* MFCC attraverso *Sphinx* [#]_.

.. figure::  /img-latex/diar_mfcc.png
   :align:   center

   Nel diagramma riportato sopra viene schematizzato il processo di acquisizione dati ed elaborazione mediante diarization.

Database
-----------

Il database del sistema è costituito da modelli GMM suddivisi per genere in cartelle denominate F (genere femminile), M (genere maschile), U (genere non riconosciuto). Ogni modello rappresenta uno speaker differente e può essere rimodellato con l'aggiunta di nuove *features*. Per la creazione del modello è infatti necessario

.. [#]Sphinx-4 è un sistema di riconoscimento vocale scritto interamentenel linguaggio di programmazione JavaTM. E' stato creato attraverso una collaborazione tra il gruppo Sfinge presso la Carnegie Mellon University, SunMicrosystems Laboratories, Mitsubishi Electric Research Labs (MERL), e HewlettPackard (HP), con il contributo dell'Università della California a Santa Cruz (UCSC) e il Massachusetts Institute of Technology (MIT).
