Abstract
========


In questo articolo viene presentato un sistema di riconoscimento vocale *Speaker Identification* che opera in modalità *offline* per l'individuazione dei differenti speakers presenti all'interno di una traccia video/audio. Il contesto di applicazione è in generale quello della segmentazione e indicizzazione automatica di video; l'impiego dell'informazione audio può dare un contributo non indifferente nella ricerca di specifici segmenti video (es. telegiornali) in cui sono presenti differenti speakers che si alternano nel parlato. 
L'applicazione si basa principalmente sul sistema di *Speaker Diarization* facente parte del progetto *LIUM*, realizzato dal Laboratorio d'Informatica dell'Università di Maine in Francia: si avvale di un tipo di classificazione *text-indipendent* ed estrae le *features* nel dominio della frequenza mentre la classificazione viene effettuata utilizzando i modelli gaussiani *Gaussian Mixture Models*. Il nostro contributo è stato principalmente quello di affiancare al sistema di classificazione un database di voci con la possibilità di identificare lo speaker solo se presente nel database stesso; allo stesso modo ci ha consentito di correggere eventuali errori conseguentemente ad una imprecisa diarization.
La parte di sperimentazione è stata condotta sulla base di tre differenti dataset: uno costituito da differenti segmenti video tratti da telegiornali nazionali, il secondo costruito su registrazioni ad hoc e l'altro costituito da segmenti audio estratti dal database *VOXFORGE* in lingua inglese. I test hanno dimostrato che ...

