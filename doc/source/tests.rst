Tests
=====
I Database utilizzati sono sostanzialmente tre: uno è stato costruito utilizzando tracce audio di telegiornali nazionali e conta di 105 voci, il secondo da registrazioni ad hoc mentre l'altro è stato realizzato sfruttando la collezione audio fornita da VoxForge [#]_.

Nel primo caso sono stati presi in considerazione segmenti audio di lunghezza variabile relativi a *speakers* presenti nei differenti *video news* esaminati: in particolar modo il *training set* si compone di 43 voci femminili e 62 voci maschili (Da correggere - mauro). 

Nel secondo caso invece, per poter esaminare meglio le prestazioni del sistema, è stato costruito un *training set* ad hoc, acquisendo 34 registrazioni di cui 22 maschili e 12 femminili di 30 secondi ciascuno, per un totale di 17 minuti.

Il terzo database è invece il risultato di un *crowdsourcing* messo in piedi da VoxForge : in particolare, è stato scelto il database di voci in lingua inglese essendo il più ricco di campioni audio. L'insieme di voci è stato quindi suddiviso in due insiemi che costituiscono per metà il *training set* e l'altra metà il *test set*. La scelta di utilizzare un database con campioni di differenti dimensioni, deriva dal fatto che il sistema può essere valutato anche sulla base della lunghezza minima richiesta per ottenere una risposta affidabile.

I *training set* presi in considerazione per la parte sperimentale sono interamente costituiti da modelli GMM per ciascun speaker registrato al sistema, mentre i *test set* contengono *feature* MFCC. 
Per ottimizzare il tempo di ricerca tra i modelli  dello speaker più simile, è stato suddiviso il database in 3 cartelle distinte per genere, F (Voci femminili), M (Voci maschili), U (Voci non definite).

.. figure::  /img-latex/confronto-thread-time-tabella2.png
 :align:   center

 Summary table.

.. figure::  /img-latex/confronto-thread-time-12.png
 :align:   center

 12 matching-score compared to the thread's number.

.. figure::  /img-latex/confronto-thread-time.png
 :align:   center

 22 matching-score compared to the thread's number.
 
Tutti i test effettuati in una prima fase si sono focalizzati sull'analisi delle prestazioni del sistema utilizzando un differente numero di processori e un numero crescente di *threads*.
I grafici mostrati in Figura 4.1 /4.2/ 4.3 sintetizzano i tempi medi di risposta ottenuti per differenti tentativi di riconoscimento utilizzando un MFCC e differenti modelli GMM presenti nel database ad hoc descritto in precedenza. Le prestazioni migliori ottenute con una piattaforma con 8 processori non superano in media il mezzo secondo di elaborazione per ciascun GMM. I risultati ottenuti con l'elaborazione in parallelo, come si può notare, migliorano con l'aumento del numero di *thread* in uso.
Tutti i campioni utilizzati  per questo test sono stati riconosciuti correttamente dal sistema.

Per valutare la segmentazione/diarization e la successiva associazione dei clusters risultanti ad uno speaker presente nel db, è stato utilizzato il database costruito su spezzoni di un telegiornale nazionale; il *test set* è invece stato realizzato prendendo altri 3 (??) video-tg della stessa rete, rendendo possibile la verifica sia della corretta segmentazione degli speaker che il loro riconoscimento. 

Test TGLa7 con un centinaio di voci nel db. Per creare il database di voci sono state usate una decina di edizioni del TGLa7 e per ogni test è stata usata una edizione di mezz’ora circa del telegiornale.
Di seguito una tabella riassuntiva:

.. figure::  /img-latex/test_tg7.png
  :align:   center

  Legenda:

  * A_A: speaker presente nel database e correttamente riconosciuto
  * U_U: speaker correttamente identificato come sconosciuto, non presente nel database e del quale non si hanno informazioni sull’identità (es. interviste a passanti)
  * U_N: speaker non presente nel database e definito quindi correttamente sconosciuto
  * U_A: speaker presente nel database ma erroneamente definito sconosciuto
  * A_B: speaker presente nel database ed erroneamente indentificato come altro speaker
  * A_U: speaker identificato erroneamente come conosciuto ma del quale non è conosciuta l’identità (vedi U_U)

(**Per Mauro test**) Allo stesso modo si può calcolare la capacità del sistema di identificare come non riconosciuti i soggetti non presenti nel database: questa viene definita *specificità* .

Infine, l’ultima serie di test effettuati per la parte sperimentale si focalizzano sulle capacità predittive del sistema; in poche parole si vuole verificare l’affidabilità del sistema ed eventualmente migliorarla formulando alcune strategie alternative. Utilizzando parte del database fornito da Voxforge si è costruito un training set di 624 GMM, un modello per ciascuno degli speakers presenti; il test set è stato invece realizzato con 2598 MFCC relativi a 162 speakers.

.. figure::  /img-latex/db_testset.png
 :align: center

I campioni utilizzati per questo test hanno lunghezze, qualità e dimensioni differenti; questo incide fortemente sulle prestazioni ma in questo modo è possibile analizzare il sistema con un input aleatorio e prevedere dei miglioramenti sulla base dell'output ottenuto.

Ogni MFCC è stato confrontato con ciascun GMM del db producendo una serie di scores utili per valutare la bontà di risposta del classificatore. Inizialmente si è preferito analizzare i risultati complessivi riguardanti l'esito del confronto tra tutti gli MFCC e tutto il database: si può notare dalla tabella sottostante una percentuale di falsi riconoscimenti non indifferente, risultato che ha reso opportuno considerare attendibile solo lo score dello *speaker* più probabile che ha una distanza dal secondo più probabile maggiore di 0.09. I falsi positivi si riducono al 3% di quelli iniziali. Questa scelta è stata effettuata sulla base dei seguenti dati: la media delle distanze tra il primo e il secondo classificato per i veri positivi si aggirava sui 0.09 mentre quella tra il primo e il secondo classificato per i falsi positivi si aggirava sui 0.02.

.. figure::  /img-latex/tabella-soglia.png
  :align: center

  Nella tabella vengono elencati  il numero di veri positivi (riconoscimento corretto), veri negativi (non riconosciuti), falsi positivi (falsi allarmi), falsi negativi (non riconosciuti erroneamente) sia nel caso di utilizzo della soglia per determinare se la classificazione è attendibile e sia nel caso non ne venga utilizzata alcuna. Questa soglia tiene invariato il numero di veri positivi mentre consente al 97% dei falsi positivi di collocarsi correttamente tra i veri negativi, diminuendo fortemente la percentuale di  falsi allarmi. 

Analizzando la lunghezza dei campioni analizzati, si è potuto notare un miglioramento della risposta del sistema all'aumentare della lunghezza stessa. 

.. figure::  /img-latex/confronti_l_wave.png
  :align:   center
 
  Sopra i 5 secondi si può notare una netta superiorità di classificazioni corrette rispetto ai compioni non correttamente riconosciuti.

Nella Figura 4.4 vengono riassunti i risultati del test.

.. figure::  /img-latex/resume_table.png
   :align:   center
	
   A = Risultati iniziali; B = Utilizzo soglia; C = Filtro su lunghezza wave maggiore di 5 secondi;  D = Filtro su lunghezza wave maggiore di 8 secondi;  E = Filtro su lunghezza wave maggiore di 10 secondi.

Un altro indicatore utile per esaminare la validità di risposta è quello della **Sensibilità** che individua la capacità del test di classificare correttamente gli speakers e che si esprime mediante la seguente formula:

.. figure::  /img-latex/sensibilita.png
   :align:   center


.. [#] VoxForge è stato istituito per raccogliere trascrizioni audio per l'utilizzo nei Sistemi di Riconoscimento Vocale come ad esempio ISIP, HTK, Julius e Sphinx. Lo scopo quindi è quello di catalogare e rendere disponibili tutti i files audio (chiamati anche *Speech Corpus*) e i modelli acustici con licenza GPL.

