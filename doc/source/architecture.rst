Flusso di elaborazione
===================
 
In questa sezione si vuole provare a descrivere con l'utilizzo di diagrammi, i vari stadi che costituiscono l'intero processo di classificazione e identificazione dello *speaker*. Inizialmente viene fatta una breve descrizione dell' acquisizione del dato audio o video in input e la sua successiva elaborazione tramite diarization, di seguito la creazione del database attraverso i modelli GMM e il conseguente processo di *matching score* tra MFCC e GMM per il riconoscimento o meno di un eventuale *speaker*.

Diarization
--------------

Il sistema supporta in input sia tracce audio che video; nel caso di un flusso video in ingresso, verrà estratto l'audio attraverso l'utilizzo della libreria **GStreamer** con le seguenti caratteristiche: WAVE file, RIFF little-endian data, Microsoft PCM, 16 bit, mono 16000 Hz.

Tramite il tool *LiumSpkrDiarization*  è possibile effettuare la segmentazione della traccia audio ripulita attraverso il *silence detector* di eventuali pause nel parlato; più precisamente la diarization restituisce un file denominato **seg**, in cui vengono elencati degli intervalli temporali etichettati attraverso una stessa label (S0, S1..Sn) ad indicare la medesima voce ed, una lettera (F, M, U) ad indicare il genere. 
Come si può notare dall'esempio sottostante estratto da un file *seg*, la diarization fornisce informazioni anche sulla qualità del wave ( S = studio, T=telefono ). Per ogni segmento viene inoltre specificato l'istante di inizio e la durata complessiva.

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

Una volta ottenuto il file **seg** abbiamo cercato di identificare i singoli speaker individuati dalla segmentazione, tagliando l'wave originale in singoli wave, uno per ogni segmento. 
Una volta ottenuti i differenti spezzoni audio per ogni speaker, si è potuto procedere con l'estrazione delle *features* MFCC attraverso *Sphinx* [#]_.

.. figure::  /img-latex/diar_mfcc.png
   :align:   center

   Nel diagramma riportato sopra viene schematizzato il processo di acquisizione dati ed elaborazione mediante diarization.

Database
-----------

Il database del sistema è costituito da modelli GMM suddivisi per genere in cartelle denominate F (genere femminile), M (genere maschile), U (genere non riconosciuto). Ogni file GMM può essere esteso con differenti modelli di uno stesso speaker: questo è utile  perché non essendoci vincoli sul canale di acquisizione dell’audio, è facile che il sistema, basandosi su un unico modello, non riconosca lo speaker che parla in ambienti o tramite mezzi molto diversi tra loro. I differenti modelli contribuiscono quindi ad una maggiore possibilità di riconoscimento sulla varietà di campioni  candidati.

Per la creazione del modello è  necessario poter usufruire del file MFCC contenente le *features* e il file **seg** del wave che ci interessa inserire nel db. 

.. figure::  /img-latex/build_gmm.png
   :align:   center
   
   L'elaborazione del modello GMM e l'inserimento nel database sulla base del genere del relativo speaker. 



Speaker recognition
-------------------------

La parte più interessante del sistema è quella relativa al riconoscimento dello speaker sulla base delle voci presenti nel database; naturalmente deve poter prevedere anche il caso in cui chi parla sia “sconosciuto” . Ogni nuova voce viene analizzata sulla base del relativo MFCC che verrà quindi confrontato con tutti i GMM presenti nel db utilizzando l'**MScore** di *Lium*: più precisamente il metodo **MScore** della libreria prende in input un file MFCC di feature audio e un file contenente uno o più modelli GMM e calcola uno score generalmente negativo, che può andare da circa -31 a circa -34, che è tanto migliore quanto è maggiore (si avvicina di più verso 0).

.. figure::  /img-latex/Mscore2.png
   :align:   center

Per ottimizzare i tempi di processazione è possibile generare una serie di thread che in concorrenza si dividono i confronti da fare tra i file GMM del database e i file MFCC dei singoli cluster; la scelta di mantenere distinti i modelli vocali dei differenti *speakers* nasce anche da questa esigenza. 

Una volta ottenuto il nome dello speaker con lo score più alto (*best score*) è necessario verificare se il risultato è attendibile: per prima cosa bisogna accertarsi che lo score sia “sufficientemente” alto per poter essere escludere la possibilità che lo speaker non sia presente nel database. Per fare questo è stato individuata una soglia in modo empirico, convergendo alla fine sul valore -33: se il *best score* risulta essere minore di tale soglia, ciò indica che probabilmente lo speaker ricercato non è presente nel database. In caso contrario verrà effettuato un altro controllo per accertare che il *best score* sia “sufficientemente” indicativo ovvero che la distanza dal secondo score classificato sia maggiore di una certa quantità: tale valore è stato ottenuto mediante differenti tests, portando a ritenere accettabile una distanza non minore a 0,07.
Nel caso in cui la distanza tra il primo e il secondo risultasse minore, si ritiene inattendibile il risultato, pertanto la voce viene considerata sconosciuta.


.. [#] Sphinx-4 è un sistema di riconoscimento vocale scritto interamentenel linguaggio di programmazione JavaTM. E' stato creato attraverso una collaborazione tra il gruppo Sfinge presso la Carnegie Mellon University, SunMicrosystems Laboratories, Mitsubishi Electric Research Labs (MERL), e HewlettPackard (HP), con il contributo dell'Università della California a Santa Cruz (UCSC) e il Massachusetts Institute of Technology (MIT).
