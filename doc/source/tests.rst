Tests
=====


I *training set* presi in considerazione per la parte sperimentale sono interamente costituiti da modelli GMM per ciascun speaker registrato al sistema, mentre i *test set* contengono *feature* MFCC. 
Tutti i test effettuati in una prima fase si sono focalizzati sull'analisi delle prestazioni del sistema utilizzando un differente numero di processori: 

.. figure::  /img-latex/confronto-thread-time-12.png
   :align:   center

   12 matching-score compared to the thread's number.

.. figure::  /img-latex/confronto-thread-time.png
   :align:   center

   22 matching-score compared to the thread's number.


.. figure::  /img-latex/confronto-thread-time-tabella2.png
   :align:   center

   Summary table.

I grafici sintetizzano i tempi medi di risposta ottenuti per differenti tentativi di riconoscimento utilizzando un MFCC e differenti modelli GMM presenti nel database ad hoc descritto in precedenza. Le prestazioni migliori ottenute con una piattaforma con 8 processori non superano in media il mezzo secondo di elaborazione per ciascun GMM. I risultati ottenuti con l'elaborazione in parallelo, come si può notare, migliorano con l'aumento del numero di *thread* in uso.
Per valutare la segmentazione/diarization e la successiva associazione dei clusters risultanti ad uno speaker presente nel db, è stato utilizzato il database costruito su spezzoni di un telegiornale nazionale; il *test set* è invece stato realizzato prendendo altri 2 (??) video-tg della stessa rete, rendendo possibile la verifica sia della corretta segmentazione degli speaker che il loro riconoscimento. Di seguito una tabella riassuntiva:

** Inserire tabella test Mauro**

** Inserire considerazioni risultati test Mauro**

Infine, l'ultima serie di test effettuati per la parte sperimentale si focalizzano sulle capacità predittive del sistema; in poche parole si vuole verificare l'affidabilità del sistema ed eventualmente migliorarla formulando alcune strategie alternative.
Utilizzando parte del database fornito da Voxforge si è costruito un *training set* di 624 GMM, un modello per ciascuno degli speakers presenti; il *test set* è stato invece realizzato con  2598 MFCC  relativi a 162 speakers. 

.. figure::  /img-latex/db_testset.png
   :align:   center

I campioni utilizzati per questo test hanno lunghezze, qualità e dimensioni differenti; questo incide fortemente sulle prestazioni ma in questo modo è possibile analizzare il sistema con un input aleatorio e prevedere dei miglioramenti sulla base dell'output ottenuto.
Ogni MFCC è stato confrontato con ciascun GMM del db producendo una serie di scores utili per valutare la bontà di risposta del classificatore. Inizialmente si è preferito analizzare i risultati complessivi riguardanti l'esito del confronto tra tutti gli MFCC e tutto il database: si può notare dalla tabella sottostante una percentuale di falsi riconoscimenti non indifferente, risultato che ha reso opportuno considerare attendibile solo lo score dello *speaker* più probabile che ha una distanza dal secondo più probabile maggiore di 0.09. I falsi positivi si riducono al 3% di quelli iniziali. Questa scelta è stata effettuata sulla base dei seguenti dati: la media delle distanze tra il primo e il secondo classificato per i veri positivi si aggirava sui 0.09 mentre quella tra il primo e il secondo classificato per i falsi positivi si aggirava sui 0.02.
Questa soglia tiene invariato il numero di veri positivi mentre consente al 97% dei falsi positivi di collocarsi correttamente tra i veri negativi, diminuendo fortemente la percentuale di errore riportata nella tabella sottostante. 

.. figure::  /img-latex/tabella-soglia.png
   :align:   center




Analizzando la lunghezza dei campioni analizzati, si è potuto notare un miglioramento della risposta del sistema all'aumentare della lunghezza stessa. 

.. figure::  /img-latex/confronti_l_wave.png
   :align:   center

Sopra i 5 secondi si può notare una netta superiorità di classificazioni corrette rispetto ai compioni non correttamente riconosciuti. 




