Database
========

I Database utilizzati sono sostanzialmente tre: uno è stato costruito utilizzando tracce audio di telegiornali nazionali e conta di 105 voci, il secondo da registrazioni ad hoc mentre l'altro è stato realizzato sfruttando la collezione audio fornita da VoxForge [#]_.
Nel primo caso sono stati presi in considerazione segmenti audio di lunghezza variabile relativi a *speakers* presenti nei differenti *video news* esaminati: in particolar modo il *training set* si compone di 43 voci femminili e 62 voci maschili (Da correggere - mauro). 
Nel secondo caso invece, per poter esaminare meglio le prestazioni del sistema, è stato costruito un *training set* ad hoc, acquisendo 34 registrazioni di cui 22 maschili e 12 femminili di 30 secondi ciascuno, per un totale di 17 minuti.
Il terzo database è invece il risultato di un *crowdsourcing* messo in piedi da VoxForge : in particolare, è stato scelto il database di voci in lingua inglese essendo il più ricco di campioni audio. L'insieme di voci è stato quindi suddiviso in due insiemi che costituiscono per metà il *training set* e l'altra metà il *test set*. La scelta di utilizzare un database con campioni di differenti dimensioni, deriva dal fatto che il sistema può essere valutato anche sulla base della lunghezza minima richiesta per ottenere una risposta affidabile.

.. [#] VoxForge è stato istituito per raccogliere trascrizioni audio per l'utilizzo nei Sistemi di Riconoscimento Vocale come ad esempio ISIP, HTK, Julius e Sphinx. Lo scopo quindi è quello di catalogare e rendere disponibili tutti i files audio (chiamati anche *Speech Corpus*) e i modelli acustici con licenza GPL.

