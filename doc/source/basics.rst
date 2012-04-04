Speaker Recognition
==========================

Per capire meglio le differenti accezioni di un sistema di riconoscimento vocale si elencano di seguito le definizioni:

*  **Speaker diarization**: segmentazione dell’audio in base alle diverse voci (timbri) presenti dipende dal contesto e dal tipo di audio (news, telefono, meeting...)

*  **Gender recognition**: riconoscimento del genere della persona (maschio-femmina)

*  **Speaker recognition**:
    *  speaker verification: viene verificata una identità: è tizio? si/no
    *  speaker identification: riconoscimento della persona (identità) sulla base di un database di speaker (chi sta parlando?)


          *  text dependent (by password)
          *  text indipendent (regardless of what is saying)

*  **Speech to text**
    *  trascrizione del testo, chiunque sia lo speaker


Il sistema di Speaker Verification/identification non prevede la parte di Diarization in quanto si presume la presenza di una sola voce nella traccia audio; è invece indispensabile una fase di training e una di testing
