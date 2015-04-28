# API documentation #

# voiceid — Voice diarization and identification module #

VoiceID is a speaker recognition/identification system written in Python, based on the LIUM Speaker Diarization (http://lium3.univ-lemans.fr/diarization/doku.php) framework.
VoiceID can process video or audio files to identify in which slices of time there is a person speaking (diarization); then it examines all those segments to identify who is speaking. To do so
uses a voice models database.
To create the database you can do a “training phase” using the script vid in interactive mode, by assigning a label to the “unknown” speakers, or you can also build yourself manually the speaker
models and put in the db using the scripts to create the gmm files.

# voiceid.db — Voice model database classes #

Module containing the voice DB relative classes.
_class_ `voiceid.db.`**GMMVoiceDB**(_path_, _thrd\_n=1_)
> A Gaussian Mixture Model voices database.
    * **path** (`* _string_`) – the voice db path


> ` ` **add\_model**(_basefilename_, _identifier_, _gender=None_, _score=None)
> > Add a gmm model to db.
      * **basefilename** (_string_) – the wave file basename and path
      * **identifier** (_string_) – the speaker in the wave
      * **gender** (_char F, M or U_) – the gender of the speaker (optional)_



> ` ` **get\_speakers**()
> > Return a dictionary where the keys are the genders and the values are a list of the available speakers models for every gender.

> ` ` **match\_voice**(_wave\_file_, _identifier_, _gender_)
> > Match the voice (wave file) versus the gmm model of ‘identifier’ in db.
      * **wave\_file** (_string_) – wave file extracted from the wave
      * **identifier** (_string_) – the speaker in the wave
      * **gender** (_char F, M or U_) – the gender of the speaker (optional)



> ` ` **remove\_model**(_wave\_file_, _identifier_, _score_, _gender_)
> > Remove a voice model from the db.
      * **wave\_file** (_string_) – the wave file name and path
      * **identifier** (_string_) – the speaker in the wave
      * **score** (_float_) – the value of
      * **gender** (_char F, M or U_) – the gender of the speaker (optional)
      * **score** (_float) – the score obtained in the voice matching(optional)_


> ` ` **set\_maxthreads**(_trd_)
> > Set the max number of threads running together for the lookup task.
      * **trd** (`* _integer_`) – max number of threads allowed to run at the same time.



> ` ` **voice\_lookup**(_wave\_file_, _gender_)
> > Look for the best matching speaker in the db for the given features file.
      * **wave\_file** (_string_) – the wave file
      * **gender** (_char F, M or U_) – the speaker gender


> Return type:        dictionary

> Returns:            a dictionary having a computed score for every voice model in the db


> ` ` **voices\_lookup**(_wave\_dictionary_)
> > Look for the best matching speaker in the db for the given features files in the dictionary.
      * **wave\_dictionary** (`* _dictionary_`) – a dict where the keys are the wave, and the values are the relative gender (char F, M or U).


> Return type:        dictionary

> Returns:            a dictionary having a computed score for every voice model in the db


_class_ `voiceid.db.`**VoiceDB**(_path_)
> A class that represent a generic voice models db.
    * **path** (`* _string_`) – the voice db path


> ` ` **add\_model**(_basefilename_, _identifier_, _gender=None_)
> > Add a voice model to the database.
      * **basefilename** (_string_) – basename including absolulute path of the voice file
      * **identifier** (_string_) – name or label of the speaker voice in the model, in a single word without special characters
      * **gender** (_char F, M or U_) – the gender of the speaker in the model



> ` ` **get\_path**()
> > Get the base path of the voice models db, where are stored the voice model files, splitted in 3 directories according to the gender (F, M, U).
> > > Return type:        string


> Returns:            the path of the voice db


> ` ` **get\_speakers**()
> > Return a dictionary where the keys are the genders and the values are a list for every gender with the available speakers models.

> ` ` **match\_voice**(_wave\_file_, _identifier_, _gender_)
> > Match the given feature file vs the specified speaker model.
      * **wave\_file** (_string_) – the wave file
      * **identifier** (_string_) – the name or label of the speaker
      * **gender** (_char F, M or U_) – the speaker gender



> ` ` **remove\_model**(_wave\_file_, _identifier_, _score_, _gender_)
> > Remove a speaker model from the database according to the score it gets by matching vs the given feature file
      * **wave\_file** (_string_) – the wave file
      * **identifier** (_string_) – the name or label of the speaker
      * **score** (_float_) – the score obtained in the voice matching
      * **gender** (_char F, M or U_) – the speaker gender



> ` ` **voice\_lookup**(_wave\_file_, _gender_)
> > Look for the best matching speaker in the db for the given features file.
      * **wave\_file** (_string_) – the wave file
      * **gender** (_char F, M or U_) – the speaker gender



> ` ` **voices\_lookup**(_wave\_dictionary_)
> > Look for the best matching speaker in the db for the given features files in the dictionary.
      * **wave\_dictionary** (`* _dictionary_`) – a dict where the keys are the wave file extracted from the wave, and the values are the relative gender (char F, M or U).


> Return type:        dictionary

> Returns:            a dictionary having a computed score for every voice model in the db

# voiceid.sr — Speaker recognition classes #

_class_ `voiceid.sr.`**Cluster**(_identifier_, _gender_, _frames_, _dirname_, _label=None_)
> A Cluster object, representing a computed cluster for a single speaker, with gender, a number of frames and environment.
    * **identifier** (_string_) – the cluster identifier
    * **gender** (_char F, M or U_) – the gender of the cluster
    * **frames** (_integer_) – total frames of the cluster
    * **dirname** (_string_) – the directory where is the cluster wave file


> ` ` **add\_speaker**(_identifier_, _score_)
> > Add a speaker with a computed score for the cluster, if a better score is already present the new score will be ignored.
      * **identifier** (_string_) – the speaker identifier
      * **score** (_float_) – score computed between the cluster wave and speaker model



> ` ` **generate\_seg\_file**(_filename_)
> > Generate a segmentation file for the cluster.
      * **filename** (`* _string_`) – the name of the seg file



> ` ` **get\_best\_five**()
> > Get the best five speakers in the db for the cluster.
> > > Return type:        array of tuple


> Returns:            an array of five most probable speakers represented by ordered tuples of the form (speaker, score) ordered by score.


> ` ` **get\_best\_speaker**()
> > Get the best speaker for the cluster according to the scores. If the speaker’spk score is lower than a fixed threshold or is too close to the second best matching voice, then it is set as
> > “unknown”.
> > > Return type:        string


> Returns:            the best speaker matching the cluster wav


> ` ` **get\_distance**()
> > Get the distance between the best speaker score and the closest speaker score.

> ` ` **get\_duration**()
> > Return cluster duration.

> ` ` **get\_gender**()
> > Get the computed gender of the Cluster.
> > > Return type:        char


> Returns:            the gender of the cluster


> ` ` **get\_m\_distance**()
> > Get the distance between the best speaker score and the mean of all the speakers’ scores.

> ` ` **get\_mean**()
> > Get the mean of all the scores of all the tested speakers for the cluster.

> ` ` **get\_name**()
> > Get the cluster name assigned by the diarization process.

> ` ` **get\_segment**(_start\_time_)
> > Return segment by start\_time

> ` ` **get\_segments**()
> > Return segments in Cluster

> ` ` **get\_speaker**()
> > Set the right speaker for the cluster if not set and returns its name.

> ` ` **has\_generated\_waves**(_dirname_)
> > Check if the wave files generated for the cluster are still present. In case you load a json file you shold not have those files.
      * **dirname** (`* _string_`) – the output dirname



> ` ` **merge**(_other_)
> > Merge the Cluster with another.
      * **other** (`* _Cluster_`) – the cluster to be merged with



> ` ` **merge\_waves**(_dirname_)
> > Take all the wave of a cluster and build a single wave.
      * **dirname** (`* _string_`) – the output dirname



> ` ` **print\_segments**()
> > Print cluster timing.

> ` ` **remove\_segment**(_start\_time_)
> > Remove segment by start\_time

> ` ` **rename**(_label_)
> > Rename the cluster and all the relative segments.
      * **label** (`* _string_`) – the new name of the cluster



> ` ` **set\_speaker**(_identifier_)
> > Set the cluster speaker identifier ‘by hand’.
      * **identifier** (`* _string_`) – the speaker name or identifier



> ` ` **to\_dict**()
> > A dictionary representation of a Cluster.
_class_ `voiceid.sr.`**Segment**(_line_)

> A Segment taken from a segmentation file, representing the smallest recognized voice time slice.
    * **line** (`* _string_`) – the line taken from a seg file


> ` ` **get\_basename**()
> > Get the basename of the original file which belong the segment.

> ` ` **get\_duration**()
> > Get the duration of the segment in frames.

> ` ` **get\_end**()
> > Get the end frame index of the segment.

> ` ` **get\_environment**()
> > Get the environment of the segment.

> ` ` **get\_gender**()
> > Get the gender of the segment.

> ` ` **get\_line**()
> > Get the line of the segment in the original seg file.

> ` ` **get\_speaker**()
> > Get the speaker identifier of the segment.

> ` ` **get\_start**()
> > Get the start frame index of the segment.

> ` ` **merge**(_otr_)
> > Merge two segments, the otr in to the original.
      * **otr** (`* _Segment_`) – the segment to be merged with



> ` ` **rename**(_identifier_)
> > Change the identifier of the segment.
      * **identifier** (`* _string_`) – the identifier of the speaker in the segment


_class_ `voiceid.sr.`**Voiceid**(_db_, _filename_, _single=False_)

> The main object that represents the file audio/video to manage.
    * **db** (_object_) – the VoiceDB database instance
    * **filename** (_string_) – the wave or video file to be processed
    * **single** (_boolean_) – set to True to force to avoid diarization (a faster approach) only in case you have just a single speaker in the file


> ` ` **add\_update\_cluster**(_label_, _cluster_)
> > Add a cluster or update an existing cluster.
      * **label** (_string_) – the cluster label (i.e. S0, S12, S44...)
      * **cluster** (_object_) – a Cluster object



> ` ` **automerge\_clusters**()
> > Check for Clusters representing the same speaker and merge them.

> ` ` **diarization**()
> > Run the diarization process. In case of single mode (single speaker in the input file) just create the seg file with silence and gender detection.

> ` ` **extract\_speakers**(_interactive=False_, _quiet=False_, _thrd\_n=1_)
> > Identify the speakers in the audio wav according to a speakers database. If a speaker doesn’t match any speaker in the database then sets it as unknown. In interactive mode it asks the
> > user to set speakers’ names.
      * **interactive** (_boolean_) – if True the user must interact to give feedback or train the computed clusters voices
      * **quiet** (_boolean_) – silent mode, no prints in batch mode
      * **thrd\_n** (_integer_) – max number of concurrent threads for voice db matches



> _static_ ` ` **from\_dict**(_db_, _json\_dict_)
> > Build a Voiceid object from json dictionary.
      * **json\_dict** (`* _dictionary_`) – the json style python dictionary representing a Voiceid object instance



> _static_ ` ` **from\_json\_file**(_db_, _json\_filename_)
> > Build a Voiceid object from json file.
      * **json\_filename** (`* _string_`) – the file containing a json style python dictionary representing a Voiceid object instance



> ` ` **generate\_seg\_file**(_set\_speakers=True_)
> > Generate a seg file according to the information acquired about the speech clustering

> ` ` **get\_cluster**(_label_)
> > Get a the cluster by a given label.
      * **label** (`* _string_`) – the cluster label (i.e. S0, S12, S44...)



> ` ` **get\_clusters**()
> > Get the clusters recognized in the processed file.

> ` ` **get\_db**()
> > Get the VoiceDB instance used.

> ` ` **get\_file\_basename**()
> > Get the basename of the current working file.

> ` ` **get\_file\_extension**()
> > Get the extension of the current working file.

> ` ` **get\_filename**()
> > Get the name of the current working file.

> ` ` **get\_speakers\_map**()
> > A dictionary map between speaker label and speaker name.

> ` ` **get\_status**()
> > Get the status of the computation. 0:’file\_loaded’, 1:’file\_converted’, 2:’diarization\_done’, 3:’trim\_done’, 4:’speakers matched’

> ` ` **get\_time\_slices**()
> > Return the time slices with all the information about start time, duration, speaker name or “unknown”, gender and sound quality (studio/phone).

> ` ` **get\_working\_status**()
> > Get a string representation of the working status.
> > > 0:’converting\_file’, 1:’diarization’, 2:’trimming’, 3:’voice matching’, 4:’extraction finished’

> ` ` **remove\_cluster**(_label_)
> > Remove and delete a cluster.
      * **label** (`* _string_`) – the cluster label (i.e. S0, S12, S44...)



> ` ` **set\_noise\_mode**(_mode_)
> > Set a diarization configuration for noisy videos

> ` ` **to\_dict**()
> > Return a JSON representation for the clustering information.

> ` ` **to\_xmp\_string**()
> > Return the Adobe XMP representation of the information about who is speaking and when. The tags used are Tracks and Markers, the ones used by Adobe Premiere for speech-to-text
> > information.

> ` ` **update\_db**(_t\_num=4_, _automerge=False_)
> > Update voice db after some changes, for example after a train session.
      * **t\_num** (_integer_) – number of contemporary threads processing the update\_db
      * **automerge** (_boolean_) – true to do the automerge or false to not do it



> ` ` **write\_json**(_dictionary=None_)
> > Write to file the json dictionary representation of the Clusters.

> ` ` **write\_output**(_mode_)
> > Write to file (basename.extension, for example: myfile.srt) the output of the recognition process.
      * **mode** (`* _string_`) – the output format: srt, json or xmp


`voiceid.sr.`**extract\_clusters**(_segfilename_, _clusters_)

> Read _clusters from segmentation file.
`voiceid.sr.`**manage\_ident**(_filebasename_,_gmm_,_clusters_)
> Take all the files created by the call of wav\_vs\_gmm() on the whole speakers db and put all the results in a bidimensional dictionary.
# voiceid.fm — Low level Wave and Gmm files manipulation #_

Module containing the low level file manipulation functions.
`voiceid.fm.`**build\_gmm**(_filebasename_, _identifier_)
> Build a gmm (Gaussian Mixture Model) file from a given wave with a speaker identifier associated.
    * **filebasename** (_string_) – the input file basename
    * **identifier** (_string_) – the name or identifier of the speaker


`voiceid.fm.`**diarization**(_filebasename_, _h\_par='3'_, _c\_par='1.5'_)
> Take a wav and wave file in the correct format and build a segmentation file. The seg file shows how much speakers are in the audio and when they talk.
    * **filebasename** (`* _string_`) – the basename of the wav file to process


`voiceid.fm.`**diarization\_standard**(_filebasename_)
> Take a wave file in the correct format and build a segmentation file. The seg file shows how much speakers are in the audio and when they talk.
    * **filebasename** (`* _string_`) – the basename of the wav file to process


`voiceid.fm.`**file2trim**(_filename_)
> Take a video or audio file and converts it into smaller waves according to the diarization process.
    * **filename** (`* _string_`) – the input file audio/video


`voiceid.fm.`**file2wav**(_filename_)
> Take any kind of video or audio and convert it to a “RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz” wave file using gstreamer. If you call it passing a wave it
> checks if in good format, else it converts the wave in the good format.
    * **filename** (`* _string_`) – the input audio/video file to convert


`voiceid.fm.`**get\_gender**(_input\_file_)
> Return gender of a given gmm file.
    * **input\_file** (`* _string_`) – the gmm file


`voiceid.fm.`**ident\_seg**(_filebasename_, _identifier_)
> Substitute cluster names with speaker names ang generate a `<filebasename>.ident.seg` file.
`voiceid.fm.`**ident\_seg\_rename**(_filebasename_, _identifier_, _outputname_)
> Take a seg file and substitute the clusters with a given name or identifier.
`voiceid.fm.`**merge\_gmms**(_input\_files_, _output\_file_)
> Merge two or more gmm files to a single gmm file with more voice models.
    * **input\_files** (_list_) – the gmm file list to merge
    * **output\_file** (_string_) – the merged gmm output file


`voiceid.fm.`**merge\_waves**(_input\_waves_, _wavename_)
> Take a list of waves and append them to a brend new destination wave.
    * **input\_waves** (_list_) – the wave files list
    * **wavename** (_string_) – the output wave file to be generated


`voiceid.fm.`**rename\_gmm**(_input\_file_, _identifier_)
> Rename a gmm with a new speaker identifier(name) associated.
    * **input\_file** (_string_) – the gmm file to rename
    * **identifier** (_string_) – the new name or identifier of the gmm model


`voiceid.fm.`**seg2srt**(_segfile_)
> Take a seg file and convert it in a subtitle file (srt).
    * **segfile** (`* _string_`) – the segmentation file to convert


`voiceid.fm.`**seg2trim**(_filebasename_)
> Take a wave and splits it in small waves in this directory structure `<file base name>/<cluster>/<cluster>_<start time>.wav`
    * **filebasename** (`* _string_`) – filebasename of the seg and wav input files


`voiceid.fm.`**split\_gmm**(_input\_file_, _output\_dir=None_)
> Split a gmm file into gmm files with a single voice model.
    * **input\_file** (_string_) – the gmm file containing various voice models
    * **output\_dir** (_string_) – the directory where is splitted the gmm input file


`voiceid.fm.`**srt2subnames**(_filebasename_, _key\_value_)
> Substitute cluster names with real names in subtitles.
`voiceid.fm.`**wav\_vs\_gmm**(_filebasename_, _gmm\_file_, _gender_, _custom\_db\_dir=None_)
> Match a wav file and a given gmm model file and produce a segmentation file containing the score obtained.
    * **filebasename** (_string_) – the basename of the wav file to process
    * **gmm\_file** (_string_) – the path of the gmm file containing the voice model
    * **gender** (_char_) – F, M or U, the gender of the voice model
    * **custom\_db\_dir** (_None or string_) – the voice models database to use


`voiceid.fm.`**wave\_duration**(_wavfile_)
> Extract the duration of a wave file in sec.
    * **wavfile** (`* _string_`) – the wave input file


# voiceid.utils — Utilities #

`voiceid.utils.`**alive\_threads**(_t\_dict_)
> Check how much threads are running and alive in a thread dictionary
    * **t\_dict** (`* _dictionary_`) – thread dictionary like { key : thread\_obj, ... }


`voiceid.utils.`**check\_cmd\_output**(_command_)
> Run a shell command and return the result as string
`voiceid.utils.`**check\_deps**()
> Check for dependencies.
`voiceid.utils.`**ensure\_file\_exists**(_filename_)
> Ensure file exists and is not empty, otherwise raise an IOError.
    * **filename** (`* _string_`) – file to check


`voiceid.utils.`**humanize\_time**(_secs_)
> Convert seconds into time format.
    * **secs** (`* _integer_`) – the time in seconds to represent in human readable format (hh:mm:ss)


`voiceid.utils.`**is\_good\_wave**(_filename_)
> Check if the wave is in correct format for LIUM.
    * **filename** (`* _string_`) – file to check


`voiceid.utils.`**start\_subprocess**(_commandline_)
> Start a subprocess using the given commandline and check for correct termination.
    * **commandline** (`* _string_`) – the command to run in a subprocess