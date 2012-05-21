Applicazione 
============

Per rendere il tool utilizzabile in maniera semplice e con un output chiaro, è stato realizzato
un'applicativo con interfaccia essenziale.

.. figure::  /img-latex/player1.png
   :align:  center
   
Come si può notare dall'immagine sopra, l'applicazione è stata realizzata con l'utilizzo di un player che rende possibile visualizzare nel video scelto gli speakers rilevati dal riconoscimento automatico. Una volta selezionato il video è infatti possibile avviare l'estrazione degli speakers che verranno successivamente visualizzati sulla sinistra del player. A questo punto è possibile, utilizzando i checkboxes, selezionare gli speakers  di proprio interesse: nell'area sottostante lo *slider* temporale del player verranno visualizzati gli intervalli in cui ciascun speaker selezionato parla, distinguendoli attraverso un colore differente assegnato a ciascuno di essi.

.. figure::  /img-latex/intervalli_speakers.png
   :align:  center

Come già descritto in precedenza, ogni *cluster* risultante dalla *diarization* viene confrontato con precedenti modelli salvati all'interno di un database: l'applicazione consente di selezionare questo database e avviare il processo per il riconoscimento. Nel caso in cui non vengano trovati, tra i modelli presenti nel db, *speakers* compatibili con le voci estratte, i relativi *clusters* verranno visualizzati con l'etichetta *unknown*: per addestrare il sistema aggiungendo tali voci sconosciute al database, basterà cliccare sulla relativa riga nella lista ed editare il nome corretto.

.. figure::  /img-latex/player2.png
    :align:  center

Tutti i dati potranno essere salvati utilizzando la *toolbar*  superiore, in formato *json*: questo consente di poter caricare direttamente un video e visualizzare le informazioni precedentemente estratte.
