# Examples #

Using the library in Python scripts is very easy, generally you use two classes, `GMMVoiceDB`, the class that represents the voice database, and `Voiceid`, the class that do all the work with a single video/audio file.

First of all you have to import the needed classes.

```
from voiceid.sr import Voiceid
from voiceid.db import GMMVoiceDB
```

Then you have to instantiate the voice database. To do that you have to call the constructor of `GMMVoiceDB` passing as parameter the directory where is the model db. It can be a new or old database, if the dir is empty will be created the db structure needed.

```
#   create voice db   

db = GMMVoiceDB('mydir')
```

Now you can add all the voices you want to the database using the `add_model` method of the db.
Usually the db has already some voice models added by the interactive mode of the `vid` script or with the gui `voiceidplayer`, which are a easy way to do that.

```
# add models to db: params the basename of 'giov_wave.wav' and the speaker, Giovanni

db.add_model('giov_wave', 'Giovanni')
db.add_model('fran_wave', 'Francesco')
db.add_model('luca_wave', 'Luca')
...
```

To check it the db actually has the models for the speakers you add, type:
```
print db.get_speakers()

# output
{'F': [],
'M': ['Giovanni','Francesco','Luca'],
'U': [] }

```


When the db is ready, you can work on the file you want to process.
To do that you have to call the `Voiceid` constructor with two parameters: the database instance and the path of the file to process.

```

# process a video/audio file containing various speakers

v = Voiceid(db, 'myfile.mp4')
```

Once loaded the file, you have to call the `extract_speakers` method of `Voiceid` to process the file.

```
# extract the speakers from file and search into db 

v.extract_speakers()

```

Now you should have all the extracted info into a list of clusters, which are objects of the class `Cluster` each representing a different Speaker. Each cluster has a list of `Segments` objects, which keep info about the speakers' voice in the audio track of the file.
This simple prints show which voices were recognized by the system.

```

# print the clusters (one for every speaker) and relative speakers' names 

for c in v.get_clusters():
    cluster = v.get_cluster(c)
    print cluster
    cluster.print_segments()
    print


# output

S0 (Luca)
00:00:42,980 to 00:00:49,140
00:00:50,040 to 00:00:53,280
00:00:54,150 to 00:00:59,500
00:00:59,590 to 00:01:01,780

S3 (Anna)
00:01:13,010 to 00:01:17,990
00:01:18,830 to 00:01:20,450
00:01:20,940 to 00:01:30,300
00:01:37,660 to 00:01:49,890
00:01:52,510 to 00:02:00,770

S4 (Giovanni)
00:05:29,630 to 00:05:31,820

S5 (Francesco)
00:02:56,260 to 00:03:13,350
00:03:13,350 to 00:03:33,210
00:03:33,210 to 00:03:37,610
00:03:37,610 to 00:03:47,340
00:03:47,700 to 00:03:51,310
00:03:51,600 to 00:03:53,660

```

In case you have no models in the db or the voices are not recognized, you could have something like:

```

S51 (unknown)
00:05:52,300 to 00:05:58,270

S71 (unknown)
00:07:51,800 to 00:08:07,210
00:08:07,210 to 00:08:14,970
00:08:18,110 to 00:08:29,500

S65 (unknown)
00:07:13,380 to 00:07:16,650
00:07:27,800 to 00:07:32,270

```

If you want to listen to the audio, you can get the wave path of the entire cluster audio joined together by typing:


```

for c in v.get_clusters():
    cluster = v.get_cluster(c)
    print cluster
    print cluster.wave
    cluster.print_segments()
    print

# output

S51 (unknown)
/the/path/of/your/file/S51.wav
00:05:52,300 to 00:05:58,270


S71 (unknown)
/the/path/of/your/file/S71.wav
00:07:51,800 to 00:08:07,210
00:08:07,210 to 00:08:14,970
00:08:18,110 to 00:08:29,500


S65 (unknown)
/the/path/of/your/file/S65.wav
00:07:13,380 to 00:07:16,650
00:07:27,800 to 00:07:32,270

```

Then you can play the Wav using your favorite library, like GStreamer, and listen.
When you know who is talking, you can set the name to the given cluster like that:

```

c = v.get_cluster('S51')
c.set_speaker('Paolo')

c = v.get_cluster('S71')
c.set_speaker('Andrea')

```

`set_speaker` doesn't do all the work, you have to tell Voiceid you have finish the work and explicitly execute the `update_db` routine. It does all the modifications scheduled, most of it are new models creation, for db consistence.

```
v.update_db()
```

Now you should have two new models in the db for "Paolo" and "Andrea".
If you run a new recognition on the same file the system should automatically recognize their voices.



This is basically what do the `vid` script. You can take a look at [it](http://code.google.com/p/voiceid/source/browse/trunk/scripts/vid) if you want to know some more info for a simple usage.
For advanced use you can take a look at the source of [`voiceidplayer`](http://code.google.com/p/voiceid/source/browse/trunk/scripts/voiceidplayer).