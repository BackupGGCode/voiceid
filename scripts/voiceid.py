#!/usr/bin/env python
#########################################################################
#
# VoiceID, Copyright (C) 2011, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it
# Web: http://code.google.com/p/voiceid
# Authors: Michela Fancello, Mauro Mereu
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#########################################################################

from optparse import OptionParser
from multiprocessing import Process, cpu_count, active_children
import os
import shlex, subprocess
import sys, signal
import time
import re
import string
import shutil
import struct

#################
#   classes
#################
class Cluster:
    """ A Cluster object, representing a computed cluster for a single speaker, with gender, a number of frames and environment """
    def __init__(self, name, gender, frames ):
        """ Constructor of a Cluster object"""
        self.gender = gender
        self.frames = frames
        self.e = None
        self.name = name
        self.speaker = None
        self.speakers = {}
        self.wave = None
        self.mfcc = None
        self.segments = []
        self.seg_header = None

    def add_speaker(self, name, value):
        """ Add a speaker with a computed score for the cluster, if a better value is already present the new value will be ignored."""
        if self.speakers.has_key( name ) == False:
            self.speakers[ name ] = float(value)
        else:
            if self.speakers[ name ] < float(value):
                self.speakers[ name ] = float(value)

    def get_speaker(self):
        """ Sets the right speaker for the cluster if not set and returns its name """
        if self.speaker == None:
            self.speaker = self.get_best_speaker()
        return self.speaker

    def get_mean(self):
        """ Get the mean of all the scores of all the tested speakers for the cluster"""
        return sum(self.speakers.values()) / len(self.speakers) 

    def get_name(self):
        """ Get the cluster name assigned by the diarization process"""
        return self.name

    def get_best_speaker(self):
        """ Get the best speaker for the cluster according to the scores. If the speaker's score is lower than a fixed threshold or is too close to the second best matching voice, then it is set as "unknown" """
        max_val = -33.0
        try:
            self.value = max(self.speakers.values())
        except:
            self.value = -100
        self.speaker = 'unknown'
        if self.value > max_val:
            for s in self.speakers:
                if self.speakers[s] == self.value:
                    self.speaker = s
                    break
        if self.get_distance() < .1:
            self.speaker = 'unknown'
        return self.speaker

    def get_distance(self):
        """ Get the distance between the best speaker score and the closest speaker score"""
        values = self.speakers.values()
        values.sort(reverse=True)
        try:
            return abs(values[1]) - abs(values[0])
        except:
            return 1000.0

    def get_m_distance(self):
        """ Get the distance between the best speaker score and the mean of all the speakers' scores""" 
        value = max(self.speakers.values())
        return abs( abs( value ) - abs( self.get_mean() ) )

    def generate_seg_file(self, filename):
        """ Generate a segmentation file for the cluster"""
        self.generate_a_seg_file(filename,self.wave[:-4])

    def generate_a_seg_file(self, filename, show):
        """ Generate a segmentation file for the given showname"""
        f = open(filename,'w')
        f.write(self.seg_header)
        line = self.segments[0][:]
        line[0]=show
        line[2]=0
        line[3]=self.frames-1
        f.write("%s %s %s %s %s %s %s %s\n" % tuple(line) )
        f.close()

    def build_and_store_gmm(self, show):
        """ Build a speaker model for the cluster and store in the main speakers db"""
        oldshow = self.wave[:-4]
        shutil.copy(oldshow+'.wav', show+'.wav')
        shutil.copy(oldshow+'.mfcc', show+'.mfcc')
        self.generate_a_seg_file(show+'.seg',show)

        ident_seg(show, self.speaker)

        train_init(show)
        try:
            ensure_file_exists(show+'.mfcc')
        except:
            extract_mfcc(show)
        train_map(show)
        ensure_file_exists(show+".gmm")
        original_gmm = os.path.join(db_dir,self.gender,self.speaker+'.gmm')
        merge_gmms([original_gmm,show+'.gmm'],original_gmm)
        if not keep_intermediate_files:
            os.remove(show+'.gmm')
            
    def to_dict(self):
        """ A dictionary representation of a Cluster """
        speaker = self.get_best_speaker()
        segs = []
        for s in self.segments:
            t = s[2:]
            t[-1] = speaker
            t[0] = int(t[0])
            t[1] = int(t[1]) 
            segs.append(t)
        return segs
    
    def print_segments(self):
        """ Print cluster timing """
        for s in self.segments:
            print "%s to %s" %( humanize_time(float(s[2])/100) , humanize_time((float(s[2])+float(s[3]))/100) )

class ClusterManager():
    """ A collection of clusters"""

    def __init__(self, clusters={}, filename = '', dict=False):
        """ Initializations"""
        self.clusters = clusters
        self.filename = ''
        self.basename = ''
        self.extension = ''       
        self.time = 0
        self.interactive = False 
        if filename != '':
            self.set_filename(filename)
            
        if dict:
            try:
                self.time = dict['duration']
                self.set_filename(dict['url'])
                sel = dict['selections']
                 
            except:
                raise Exeption('problems in ClusterManager initialization')
    
    def __iter__(self):
        """ Just iterate over the cluster dictionary"""
        return self.clusters.__iter__()
    
    def set_filename(self,filename):
        """ Set the filename of the current working file"""
        self.filename = filename
        self.basename, self.extension = os.path.splitext(self.filename)
        
    def get_filename(self):
        """ Get the name of the current working file"""
        return self.filename
        
    def get_file_basename(self):
        """ Get the basename of the current working file"""
        return self.basename[:]
    
    def get_file_extension(self):
        """ Get the extension of the current working file"""
        return self.extension[:]
        
    def get_cluster(self,identifier):
        """ Get a the cluster by a given identifier"""
        return self.clusters[identifier]
    
    def add_update_cluster(self, identifier, cluster):
        """ Add a cluster or update an existing cluster"""
        self.clusters[identifier] = cluster
        
    def remove_cluster(self,identifier):
        """ Remove the cluster from the cluster manager"""
        del self.clusters[identifier]
        
    def get_time_slices(self):
        """ Returns the time slices with all the information about start time, duration, speaker name or "unknown", gender and sound quality (studio/phone)"""
        tot = []
        for c in self.clusters:
            tot.extend(self.get_cluster(c).to_dict()[:])
        tot.sort()
        return tot

    def get_speakers_map(self):
        """ A dictionary map between speaker label and speaker name"""
        speakers = {}
        for c in self:
            speakers[c] = cmanager.get_cluster(c).get_best_speaker()
        return speakers

    def to_XMP_string(self):
        """ Returns the Adobe XMP representation of the information about who is speaking and when. The tags used are Tracks and Markers, the ones used by Adobe Premiere for speech-to-text information.
        ...
        <xmpDM:Tracks>
            <rdf:Bag>
                <rdf:li>
                    <rdf:Description
                     xmpDM:trackName="Speaker identification">
                        <xmpDM:markers>
                            <rdf:Seq>
                                <rdf:li
                                 xmpDM:startTime="310"
                                 xmpDM:duration="140"
                                 xmpDM:speaker="Speaker0"
                                 />
                                <rdf:li
                                 xmpDM:startTime="450"
                                 xmpDM:duration="60"
                                 xmpDM:speaker="Speaker0"
                                 />
                            </rdf:Seq>
                        </xmpDM:markers>
                    </rdf:Description>
                </rdf:li>
            </rdf:Bag>
        </xmpDM:Tracks>
        ...
        """
        initial_tags = """<?xml version="1.0"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description  xmlns:xmpDM="http://ns.adobe.com/xmp/1.0/DynamicMedia/">
            <xmpDM:Tracks>
                <rdf:Bag>
                    <rdf:li>
                        <rdf:Description
                         xmpDM:trackName="Speaker identification">
                            <xmpDM:markers>
                                <rdf:Seq>"""
        inner_string = '' 
        for s in self.get_time_slices():
            inner_string +="""    
                                    <rdf:li
                                     xmpDM:startTime="%s"
                                     xmpDM:duration="%s"
                                     xmpDM:speaker="%s"
                                     /> """ % (s[0], s[1], s[-1] )
        
        final_tags = """
                                </rdf:Seq>
                            </xmpDM:markers>
                        </rdf:Description>
                    </rdf:li>
                </rdf:Bag>
            </xmpDM:Tracks>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>
"""
        #TODO: extract previous XMP information from the media and merge with speaker information
        return initial_tags+inner_string+final_tags            

    
    def to_dict(self):
        """ Returns a JSON representation for the clustering information. The JSON model used is like:
        <code>
{
    "duration": 15,
    "url": "url1",
    "selections": [{
        "annotations": [{
            "author": "User",
            "description": "my description",
            "keyword": "mykeyword",
            "lang": "EN"
        }, {
            "author": "User",
            "description": "la mia descrizione",
            "keyword": "parola chiave",
            "lang": "IT"
        }],
        "resolution": "0x0",
        "selW": 20,
        "selH": 15,
        "selY": 10,
        "selX": 10,
        "startTime" : 0,
        "endTime" : 10
        
    }]
}
        </code>
        
        """
        
        dict = {"duration":self.time,
                "url": self.filename,
                "selections": []
                }
        
        for s in self.get_time_slices():
            dict['selections'].append({        
                                     "resolution": "0x0",
                                     "selW": 0,
                                     "selH": 0,
                                     "selY": 0,
                                     "selX": 0,                   
                                     "startTime" : float(s[0])/1000,
                                     "endTime" : float(s[0]+s[1])/1000,
                                     "annotations": [{'author': '',
                                                      'description': '',
                                                      'keyword' : s[-1],
                                                      'lang' : 'EN'
                                                      }]
                                     })
        #TODO: define a way to fill missing fields
        return dict

    def write_json(self,dict=None):
        """ Write to file the json dict representation of the Clusters"""
        if not dict:
            dict = self.to_dict()
        prefix = ''
        if self.interactive:
            prefix = '.interactive'
        
        file = open(self.get_file_basename()+prefix+'.json','w')
        file.write(str(dict))
        file.close()

    def write_output(self,format):
        """ Write to file (basename.extension, for example: myfile.srt) the output of   """
        
        if format == 'srt':
            seg2srt(self.get_file_basename()+'.seg')
            srt2subnames(self.get_file_basename(), self.get_speakers_map()) # build subtitles - the main output at this time
            shutil.move(self.get_file_basename()+'.ident.srt', self.get_file_basename()+'.srt')
            
        if format == 'json':
            self.write_json()
        
        if format == 'xmp':
            file = open(self.get_file_basename()+'.xmp','w')
            file.write(str(self.to_XMP_string()))
            file.close()


#############################################
# initializations and global variables
#############################################
lium_jar = os.path.expanduser('~/.voiceid/lib/LIUM_SpkDiarization-4.7.jar')  # http://lium3.univ-lemans.fr/diarization/doku.php
ubm_path  = os.path.expanduser('~/.voiceid/lib/ubm.gmm')
test_path  = os.path.expanduser('~/.voiceid/test')
db_dir = os.path.expanduser('~/.voiceid/gmm_db')
output_format = 'srt' #default output format
quiet_mode = False

verbose = False
keep_intermediate_files = False

dev_null = open('/dev/null','w')
if verbose:
        dev_null = None

cmanager = ClusterManager()


#################################
#  utils
#################################
def start_subprocess(commandline):
    """ Starts a subprocess using the given commandline and checks for correct termination """
    args = shlex.split(commandline)
    #print commandline
    p = subprocess.Popen(args, stdin=dev_null,stdout=dev_null, stderr=dev_null)
    retval = p.wait()
    if retval != 0:
        raise Exception("Subprocess %s closed unexpectedly [%s]" %  (str(p), commandline) )

def ensure_file_exists(filename):
    """ Ensure file exists and is not empty, otherwise raise an Exception """
    if not os.path.exists(filename):
        raise Exception("File %s not correctly created"  % filename)
    if not (os.path.getsize(filename) > 0):
        raise Exception("File %s empty"  % filename)

def check_deps():
    """ Check for dependency """
    ensure_file_exists(lium_jar)

    dir_m = os.path.join(db_dir,"M")
    dir_f = os.path.join(db_dir,"F")
    dir_u = os.path.join(db_dir,"U")
    ensure_file_exists(ubm_path)
    if not os.path.exists(db_dir):
        raise Exception("No gmm db directory found in %s (take a look to the configuration, db_dir parameter)" % db_dir )
    if os.listdir(db_dir) == []:
        print "WARNING: Gmm db directory found in %s is empty" % db_dir
#               raise Exception("Gmm db directory found in %s is empty" % db_dir )
    if not os.path.exists(dir_m):
        os.makedirs(dir_m)
    if not os.path.exists(dir_f):
        os.makedirs(dir_f)
    if not os.path.exists(dir_u):
        os.makedirs(dir_u)


def humanize_time(secs):
    """ Convert seconds into time format """
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return '%02d:%02d:%02d,%s' % (hours, mins, int(secs), str(("%0.3f" % secs ))[-3:] )

############################
# wave files management
############################
def wave_duration(wavfile):
    """ Extract the duration of a wave file in sec """
    import wave
    w = wave.open(wavfile)
    par = w.getparams()
    w.close()
    return par[3]/par[2]

def merge_waves(input_waves,wavename):
    """ Takes a list of waves and append them all to a brend new destination wave """
    #if os.path.exists(wavename):
            #raise Exception("File gmm %s already exist!" % wavename)
    waves = [w.replace(" ","\ ") for w in input_waves]
    w = " ".join(waves)
    commandline = "sox "+str(w)+" "+ str(wavename)
    start_subprocess(commandline)


def video2wav(show):
    """ Takes any kind of video or audio and convert it to a "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz" wave file using gstreamer. If you call it passing a wave it checks if in good format, otherwise it converts the wave in the good format """
    def is_bad_wave(show):
        """ Check if the wave is in correct format for LIUM required input file """
        import wave
        par = None
        try:
            w = wave.open(show)
            par = w.getparams()
            w.close()
        except Exception,e:
            print e
            return True
        if par[:3] == (1,2,16000) and par[-1:] == ('not compressed',):
            return False
        else:
            return True

    name, ext = os.path.splitext(show)
    if ext != '.wav' or is_bad_wave(show):
        start_subprocess( "gst-launch filesrc location='"+show+"' ! decodebin ! audioresample ! 'audio/x-raw-int,rate=16000' ! audioconvert ! 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1' ! wavenc ! filesink location="+name+".wav " )
    ensure_file_exists(name+'.wav')

######################################
# gmm files management
######################################
def merge_gmms(input_files,output_file):
    """ Merge two or more gmm files to a single gmm file with more voice models."""
    num_gmm = 0
    gmms = ''

    for f in input_files:
        try:
            current_f = open(f,'r')
        except:
            continue

        kind = current_f.read(8)
        if kind != 'GMMVECT_' :
            raise Exception('different kinds of models!')

        num = struct.unpack('>i', current_f.read(4) )
        num_gmm += int(num[0])

        all_other = current_f.read()
        gmms += all_other
        current_f.close()

    num_gmm_string = struct.pack('>i', num_gmm)
    new_gmm = open(output_file,'w')
    new_gmm.write( "GMMVECT_" )
    new_gmm.write(num_gmm_string)
    new_gmm.write(gmms)
    new_gmm.close()

def split_gmm(input_file, output_dir=None):
    """ Splits a gmm file into gmm files with a single voice model"""
    def read_gaussian(f):
        g_key = f.read(8)     #read string of 8bytes kind
        if g_key != 'GAUSS___':
            raise Exception("Error: the gaussian is not of GAUSS___ key  (%s)" % g_key)
        g_id = f.read(4)
        g_length = f.read(4)     #readint 4bytes representing the name length
        g_name = f.read( int( struct.unpack('>i',   g_length )[0] )  )
        g_gender = f.read(1)
        g_kind = f.read(4)
        g_dim = f.read(4)
        g_count = f.read(4)
        g_weight = f.read(8)

        dimension = int( struct.unpack('>i',   g_dim )[0] )

        g_header = g_key + g_id + g_length + g_name + g_gender + g_kind + g_dim + g_count + g_weight

        data = ''
        datasize = 0
        if g_kind == FULL:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < dimension :
                    datasize += 1
                    t+=1
        else:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < j+1 :
                    datasize += 1
                    t+=1

        return g_header + f.read(datasize * 8)

    def read_gaussian_container(f):
        #gaussian container
        ck = f.read(8)    #read string of 8bytes
        if ck != "GAUSSVEC":
            raise Exception("Error: the gaussian container is not of GAUSSVEC kind %s" % ck)
        cs = f.read(4)    #readint 4bytes representing the size of the gaussian container
        stuff = ck + cs
        for index in range( int( struct.unpack( '>i', cs )[0] ) ):
            stuff += read_gaussian(f)
        return stuff

    def read_gmm(f):
        myfile = {}
        #single gmm

        k = f.read(8)     #read string of 8bytes kind
        if k != "GMM_____":
            raise Exception("Error: Gmm section doesn't match GMM_____ kind")
        h = f.read(4)     #readint 4bytes representing the hash (backward compatibility)
        l = f.read(4)     #readint 4bytes representing the name length
        name = f.read( int( struct.unpack('>i',   l )[0] )  )
                          #read string of l bytes
        myfile['name'] = name
        g = f.read(1)     #read a char representing the gender
        gk = f.read(4)    #readint 4bytes representing the gaussian kind
        dim = f.read(4)   #readint 4bytes representing the dimension
        c = f.read(4)     #readint 4bytes representing the number of components
        gvect_header =  k + h + l + name + g + gk + dim + c
        myfile['header'] = gvect_header
        myfile['content'] = read_gaussian_container(f)
        return myfile


    f = open(input_file,'r')
    key = f.read(8)
    if key != 'GMMVECT_':  #gmm container
        raise Exception('Error: Not a GMMVECT_ file!')
    size = f.read(4)
    num = int(struct.unpack( '>i', size )[0]) #number of gmms
    main_header = key + struct.pack( '>i', 1 )
    FULL = 0
    files = []
    for n in range(num):
        files.append( read_gmm( f ) )

    f.close()

    file_basename = input_file[:-4]

    index = 0
    basedir,filename = os.path.split(file_basename)
    if output_dir != None:
        basedir = output_dir
        for f in files:
            newname = os.path.join( basedir, "%s%04d.gmm" % (filename, index) )
        fd = open( newname, 'w' )
        fd.write( main_header + f['header'] + f['content'] )
        fd.close()
        index += 1

def build_gmm(show,name):
    """ Build a gmm (Gaussian Mixture Model) file from a given wave with a speaker identifier (name)  associated """

    diarization(show)

    ident_seg(show,name)

    extract_mfcc(show)

    train_init(show)

    train_map(show)

#######################################
#   seg files and trim functions
#######################################
def seg2trim(segfile):
    """ Take a wave and splits it in small waves in this directory structure <file base name>/<cluster>/<cluster>_<start time>.wav """
    basename, extension = os.path.splitext(segfile)
    s = open(segfile,'r')
    for line in s.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            clust = arr[7]
            st = float(arr[2])/100
            end = float(arr[3])/100
            try:
                mydir = os.path.join(basename, clust)
                os.makedirs( mydir )
            except os.error as e:
                if e.errno == 17:
                    pass
                else:
                    raise os.error
            wave_path = os.path.join( basename, clust, "%s_%07d.%07d.wav" % (clust, int(st), int(end) ) )
            commandline = "sox %s.wav %s trim  %s %s" % ( basename, wave_path, st, end )
            start_subprocess(commandline)
            ensure_file_exists( wave_path )
    s.close()

def seg2srt(segfile):
    """ Takes a seg file and convert it in a subtitle file (srt) """
    def readtime(aline):
        return int(aline[2])

    basename, extension = os.path.splitext(segfile)
    s = open(segfile,'r')
    lines = []
    for line in s.readlines():
        if not line.startswith(";;"):
            arr=line.split()
            lines.append(arr)
    s.close()

    lines.sort(key=readtime, reverse=False)
    fileoutput = basename+".srt"
    srtfile = open(fileoutput,"w")
    row = 0
    for line in lines:
        row = row +1
        st = float(line[2])/100
        en = st+float(line[3])/100
        srtfile.write(str(row)+"\n")
        srtfile.write(humanize_time(st) + " --> " + humanize_time(en) +"\n")
        srtfile.write(line[7]+"\n")
        srtfile.write(""+"\n")

    srtfile.close()
    ensure_file_exists(basename+'.srt')

def extract_mfcc(show):
    """ Extract audio features from the wave file, in particular the mel-frequency cepstrum using a sphinx tool """
    commandline = "sphinx_fe -verbose no -mswav yes -i %s.wav -o %s.mfcc" %  ( show, show )
    start_subprocess(commandline)
    ensure_file_exists(show+'.mfcc')

def ident_seg(showname,name):
    """ Substitute cluster names with speaker names ang generate a "<showname>.ident.seg" file """
    ident_seg_rename(showname,name,showname+'.ident')


def ident_seg_rename(showname,name,outputname):
    """ Takes a seg file and substitute the clusters with a given name or identifier """
    f = open(showname+'.seg','r')
    clusters=[]
    lines = f.readlines()
    for line in lines:
        for k in line.split():
            if k.startswith('cluster:'):
                prefix,c = k.split(':')
                clusters.append(c)
    f.close()
    output = open(outputname+'.seg', 'w')
    clusters.reverse()
    for line in lines:
        for c in clusters:
            line = line.replace(c,name)
        output.write(line+'\n')
    output.close()
    ensure_file_exists(outputname+'.seg')

def manage_ident(showname, gmm, clusters):
    """ Takes all the files created by the call of mfcc_vs_gmm() on the whole speakers db and put all the results in a bidimensional dictionary """
    f = open("%s.ident.%s.seg" % (showname,gmm ) ,"r")
    for l in f:
        if l.startswith(";;"):
           cluster, speaker = l.split()[ 1 ].split(':')[ 1 ].split('_')
           i = l.index('score:'+speaker) + len('score:'+speaker+" = ")
           ii = l.index(']',i) -1
           value = l[i:ii]
           clusters[ cluster ].add_speaker( speaker, value )
           """
           if clusters[ cluster ].has_key( speaker ) == False:
               clusters[ cluster ][ speaker ] = float(value)
           else:
               if clusters[ cluster ][ speaker ] < float(value):
                   clusters[ cluster ][ speaker ] = float(value)
           """
    f.close()
    if not keep_intermediate_files:
        os.remove("%s.ident.%s.seg" % (showname,gmm ) )

def extract_clusters(filename, clusters):
    """ Read clusters from segmentation file """
    f = open(filename,"r")
    last_cluster = None
    for l in f:
        if l.startswith(";;"):
           speaker_id = l.split()[1].split(':')[1]
           clusters[ speaker_id ] = Cluster(name=speaker_id, gender='U', frames=0)
           last_cluster = clusters[ speaker_id ]
           last_cluster.seg_header = l
        else:
           line = l.split()
           last_cluster.segments.append(line)
           last_cluster.frames += int(line[3])
           last_cluster.gender =  line[4]
           last_cluster.e =  line[5]
    f.close()

def srt2subnames(showname, key_value):
    """ Substitute cluster names with real names in subtitles """

    def replace_words(text, word_dic):
        """
        take a text and replace words that match a key in a dictionary with
        the associated value, return the changed text
        """
        rc = re.compile('|'.join(map(re.escape, word_dic)))

        def translate(match):
            return word_dic[match.group(0)]+'\n'

        return rc.sub(translate, text)

    file_original_subtitle = open(showname+".srt")
    original_subtitle = file_original_subtitle.read()
    file_original_subtitle.close()
    key_value = dict(map(lambda (key, value): (str(key)+"\n", value), key_value.items()))
    text = replace_words(original_subtitle, key_value)
    out_file = showname+".ident.srt"
    # create a output file
    fout = open(out_file, "w")
    fout.write(text)
    fout.close()
    ensure_file_exists(out_file)


def video2trim(videofile):
    """ Takes a video or audio file and converts it into smaller waves according to the diarization process """
    if not quiet_mode: print "*** converting video to wav ***"
    video2wav(videofile)
    show, ext = os.path.splitext(videofile)
    if not quiet_mode: print "*** diarization ***"
    diarization(show)
    if not quiet_mode: print "*** trim ***"
    seg2trim(show+'.seg')


#############################################
#   diarization and voice matching functions
#############################################
def diarization(showname):
    """ Takes a wave file in the correct format and build a segmentation file. The seg file shows how much speakers are in the audio and when they talk """
    start_subprocess( 'java -Xmx2024m -jar '+lium_jar+' --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering ' +  showname )
    ensure_file_exists(showname+'.seg')


def train_init(show):
    """ Train the initial speaker gmm model """
    commandline = 'java -Xmx256m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=%s.ident.seg --fInputMask=%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask='+ubm_path+' --tOutputMask=%s.init.gmm '+show
    start_subprocess(commandline)
    ensure_file_exists(show+'.init.gmm')

def train_map(show):
    """ Train the speaker model using a MAP adaptation method """
    commandline = 'java -Xmx256m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=%s.ident.seg --fInputMask=%s.mfcc --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm ' + show 
    start_subprocess(commandline)
    ensure_file_exists(show+'.gmm')

def mfcc_vs_gmm(showname, gmm, gender,custom_db_dir=None):
    """ Match a mfcc file and a given gmm model file """
    database = db_dir
    if custom_db_dir != None:
        database = custom_db_dir
    gmm_dir, gmm_name = os.path.split(gmm)
    commandline = 'java -Xmx256M -Xms256M -cp ' + lium_jar + '  fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg   --fInputMask=%s.mfcc  --sOutputMask=%s.ident.' + gender + '.' + gmm_name + '.seg --sOutputFormat=seg,UTF8  --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:0:300:4" --tInputMask=' + database + '/' + gender + '/' + gmm + ' --sTop=8,' + ubm_path + '  --sSetLabel=add --sByCluster ' + showname 
    start_subprocess(commandline)
    ensure_file_exists(showname + '.ident.' + gender + '.' + gmm_name + '.seg')

def threshold_tuning():
    """ Get a score to tune up the threshold to define when a speaker is unknown"""
    showname = os.path.join(test_path,'mr_arkadin')
    gmm = "mrarkadin.gmm"
    gender = 'M'
    ensure_file_exists(showname+'.wav')
    ensure_file_exists( os.path.join(test_path,gender,gmm ) )
    video2trim(showname+'.wav')
    extract_mfcc(showname)
    mfcc_vs_gmm(showname, gmm, gender,custom_db_dir=test_path)
    clusters = {}
    extract_clusters(showname+'.seg',clusters)
    manage_ident(showname,gender+'.'+gmm,clusters)
    return clusters['S0'].speakers['mrarkadin']

###############################################
#   main functions
###############################################
def extract_speakers(file_input,interactive=False,quiet=False):
    """ Takes a file input and identifies the speakers in it according to a speakers database. 
    If a speaker doesn't match any speaker in the database then sets it as unknown """
    cpus = cpu_count()
    clusters = {}
    start_time = time.time()
    video2trim( file_input )
    diarization_time = time.time() - start_time
    cmanager.set_filename(file_input)
    basename = cmanager.get_file_basename()
    extract_mfcc( basename )

    if not quiet: print "*** voice matching ***"
    extract_clusters( "%s.seg" %  basename, cmanager.clusters )
    
#    cmanager.clusters = clusters
    #print "*** build 1 wave 4 cluster ***"
    for cluster in cmanager:
        name = cluster
        videocluster =  os.path.join(basename,name)
        listwaves = os.listdir(videocluster)
        listw = [os.path.join(videocluster, f) for f in listwaves]
        show = os.path.join(basename,name)
        cmanager.get_cluster(cluster).wave = os.path.join(basename,name+".wav")
        merge_waves(listw,cmanager.get_cluster(cluster).wave)
        extract_mfcc(show)
        cmanager.get_cluster(cluster).generate_seg_file(show+".seg")

    """Wave,seg(prendendo le info dal seg originale) e mfcc per ogni cluster
    Dal seg prendo il genere
    for mfcc for db_genere"""

    #print "*** MScore ***"
    p = {}
    files_in_db = {}
    files_in_db["M"] = [ f for f in os.listdir(os.path.join(db_dir,"M")) if f.endswith('.gmm') ]
    files_in_db["F"] = [ f for f in os.listdir(os.path.join(db_dir,"F")) if f.endswith('.gmm') ]
    files_in_db["U"] = [ f for f in os.listdir(os.path.join(db_dir,"U")) if f.endswith('.gmm') ]
    for cluster in cmanager:
        files = files_in_db[cmanager.get_cluster(cluster).gender]
        showname = os.path.join(basename,cluster)
        for f in files:

            if  len(active_children()) < cpus :
                p[f+cluster] = Process(target=mfcc_vs_gmm, args=( showname, f, cmanager.get_cluster(cluster).gender) )
                p[f+cluster].start()
            else:
                while len(active_children()) >= cpus:
                    #print active_children()
                    time.sleep(1)
                p[f+cluster] = Process(target=mfcc_vs_gmm, args=( showname, f, cmanager.get_cluster(cluster).gender ) )
                p[f+cluster].start()
    for proc in p:
        #print active_children()
        if p[proc].is_alive():
            p[proc].join()

    for cluster in cmanager:
        files = files_in_db[cmanager.get_cluster(cluster).gender]
        showname = os.path.join(basename,cluster)
        for f in files:
            manage_ident( showname,cmanager.get_cluster(cluster).gender+"."+f , cmanager.clusters)

    if not quiet: print ""
    speakers = {}
    for c in cmanager:
        if not quiet: 
            print "**********************************"
            print "speaker ", c
            if interactive: cmanager.get_cluster(c).print_segments()
        speakers[c] = cmanager.get_cluster(c).get_best_speaker()
        gender = cmanager.get_cluster(c).gender
        if not interactive: 
            for speaker in cmanager.get_cluster(c).speakers:
                if not quiet: print "\t %s %s" % (speaker , cmanager.get_cluster(c).speakers[ speaker ])
            if not quiet: print '\t ------------------------'
        try:
            distance = cmanager.get_cluster(c).get_distance()
        except:
            distance = 1000.0
        try:
            mean = cmanager.get_cluster(c).get_mean()
            m_distance = cmanager.get_cluster(c).get_m_distance()
        except:
            mean = 0
            m_distance = 0


        proc = {}
        if interactive == True:
            cmanager.interactive = True
            best = interactive_training(basename,c,speakers[c])
            old_s = speakers[c]
            speakers[c] = best
            cmanager.get_cluster(c).speaker = best
            if speakers[c] != "unknown" and  old_s!=speakers[c]:
                videocluster = os.path.join(basename,c) #cluster directory
                listwaves = os.listdir(videocluster) #all cluster's waves
                listw = [os.path.join(videocluster, f) for f in listwaves] #all cluster's waves with absolute path
                folder_db_dir = os.path.join(db_dir,gender)
                if os.path.exists(os.path.join(folder_db_dir,old_s+".gmm")):
                    folder_tmp = os.path.join(folder_db_dir,old_s+"_tmp_gmms")
                    if not os.path.exists(folder_tmp):
                        os.mkdir(folder_tmp)
                    split_gmm(os.path.join(folder_db_dir,old_s+".gmm"),folder_tmp)
                    listgmms = os.listdir(folder_tmp)
                    showname = os.path.join(basename, c)
                    value_old_s = cmanager.get_cluster(c).value
                    if not quiet: print "value old %s" %value_old_s
                    if len(listgmms) != 1:
                        for gmm in listgmms:
                            mfcc_vs_gmm(showname, os.path.join(old_s+"_tmp_gmms",gmm), gender)
                            f = open("%s.ident.%s.%s.seg" % (showname, gender, gmm) , "r")
                            for l in f:
                                if l.startswith(";;"):
                                    cluster, speaker = l.split()[ 1 ].split(':')[ 1 ].split('_')
                                    i = l.index('score:' + speaker) + len('score:' + speaker + " = ")
                                    ii = l.index(']', i) - 1
                                    value_tmp = l[i:ii]
                                    if not quiet: print "value tmp %s" %float(value_tmp)
                                    if float(value_tmp) == value_old_s:
                                        os.remove(os.path.join(folder_tmp, gmm))
                        merge_gmms(listgmms, os.path.join(folder_db_dir,old_s+".gmm"))
                    else:
                        os.remove(os.path.join(folder_db_dir,old_s+".gmm"))
    
                    shutil.rmtree(folder_tmp)
                cont = 0
                gmm_name = speakers[c]+".gmm"
                wav_name = speakers[c]+".wav"
                if os.path.exists(wav_name):
                    while True: #search an inexistent name for new gmm
                        cont = cont +1
                        gmm_name = speakers[c]+""+str(cont)+".gmm"
                        wav_name = speakers[c]+""+str(cont)+".wav"
                        if not os.path.exists(wav_name):
                            break
                basename_file, extension_file = os.path.splitext(wav_name)
                #show=wav_name
                #basename_wave =
                merge_waves(listw,wav_name)
                if not quiet: print "name speaker %s " % speakers[c]

                def build_gmm_wrapper(basename_file, cluster):
                    cmanager.get_cluster(cluster).build_and_store_gmm(basename_file)
                    if not keep_intermediate_files:
                        os.remove("%s.wav" % basename_file )
                        os.remove("%s.seg" % basename_file )
                        os.remove("%s.mfcc" % basename_file )
                        os.remove("%s.ident.seg" % basename_file )
                        os.remove("%s.init.gmm" % basename_file )
                proc[c] = Process( target=build_gmm_wrapper, args=(basename_file,c) )
                proc[c].start()
        if not interactive:
            if not quiet: print '\t best speaker: %s (distance from 2nd %f - mean %f - distance from mean %f ) ' % (speakers[c] , distance, mean, m_distance)    
    
    sec = wave_duration(basename+'.wav')
    total_time = time.time() - start_time
    cmanager.time = total_time
    if interactive:
        print "Waiting for working processes"
        for p in proc:
            if proc[p].is_alive():
                proc[p].join()
    if not interactive:
        if not quiet: print "\nwav duration: %s\nall done in %dsec (%s) (diarization %dsec time:%s )  with %s cpus and %d voices in db (%f)  " % ( humanize_time(sec), total_time, humanize_time(total_time), diarization_time, humanize_time(diarization_time), cpus, len(files_in_db['F'])+len(files_in_db['M'])+len(files_in_db['U']), float(total_time - diarization_time )/len(files_in_db) )

def interactive_training(videoname,cluster,speaker):
    """ A user interactive way to set the name to an unrecognized voice of a given cluster """
    info = None
    p = None
    if speaker == "unknown":
        info = """The system has not identified this speaker!"""
    else:
        info = "The system has identified this speaker as '"+speaker+"'!"

    print info

    while True:
        char = raw_input("\n 1) Listen\n 2) Set name\n Press enter to skip\n> ")
        print ''
        if p != None and p.poll() == None:
            p.kill()
        if char == "1":
            videocluster = str(videoname+"/"+cluster)
            listwaves = os.listdir(videocluster)
            listw = [os.path.join(videocluster, f) for f in listwaves]
            w = " ".join(listw)
            commandline = "play "+str(w)
            print "  Listening %s..." % cluster
            args = shlex.split(commandline)
            p = subprocess.Popen(args, stdin=dev_null, stdout=dev_null, stderr=dev_null)
            time.sleep(1)
            continue
        if char == "2":
            m = False
            while not m:
                name = raw_input("Type speaker name or leave blank for unknown speaker: ")
                while True:
                    if len(name) == 0:
                        name = "unknown"
                    ok = raw_input("Save as '"+name+"'? [Y/n/m] ")
                    if ok in ('y', 'ye', 'yes',''):
                        return name
                    if ok in ('n', 'no', 'nop', 'nope'):
                        break
                    if ok in ('m',"menu"):
                        m = True
                        break
                    
                if not m: 
                    print "Yes, no or menu, please!"  
            continue
        if char == "":
            return speaker
        print "Type 1, 2 or enter to skip, please"
    
        
##################################
# argument parsing facilities
##################################
def remove_blanks_callback(option, opt_str, value, parser):
    """ Remove all white spaces in filename and substitute with underscores"""
    if len(parser.rargs) == 0:
        parser.error("incorrect number of arguments")
    file_input=str(parser.rargs[0])
    new_file_input = file_input
    new_file_input=new_file_input.replace("'",'_').replace('-','_').replace(' ','_')
    try:
        shutil.copy(file_input,new_file_input)
    except shutil.Error, e:
        if  str(e) == "`%s` and `%s` are the same file" % (file_input,new_file_input):
            pass
        else:
            raise e
    ensure_file_exists(new_file_input)
    file_input=new_file_input
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, file_input)

def multiargs_callback(option, opt_str, value, parser):
    """ Create an array from multiple args"""
    if len(parser.rargs) == 0:
        parser.error("incorrect number of arguments")
    args=[]
    for arg in parser.rargs:
        if arg[0] != "-":
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)

##############################################################
#  the actual main - argument parsing and functions calls
##############################################################
if __name__ == '__main__':
    usage = """%prog ARGS

examples:
    speaker identification
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -i INPUT_FILE
    
        user interactive mode
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -i INPUT_FILE -u    

    speaker model creation
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g INPUT_FILE
        %prog [ -d GMM_DB ] [ -j JAR_PATH ] [ -b UBM_PATH ] -s SPEAKER_ID -g WAVE WAVE ... WAVE  MERGED_WAVES """

    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="verbose mode")
    parser.add_option("-q", "--quiet", dest="quiet_mode", action="store_true", default=False, help="suppress prints")
    parser.add_option("-k", "--keep-intermediatefiles", dest="keep_intermediate_files", action="store_true", help="keep all the intermediate files")
    parser.add_option("-i", "--identify", action="callback",callback=remove_blanks_callback, dest="file_input", metavar="FILE", help="identify speakers in video or audio file")
    parser.add_option("-g", "--gmm", action="callback", callback=multiargs_callback, dest="waves_for_gmm", help="build speaker model ")
    parser.add_option("-s", "--speaker", dest="speakerid", help="speaker identifier for model building")
    parser.add_option("-d", "--db",type="string", dest="dir_gmm", metavar="PATH",help="set the speakers models db path (default: %s)" % db_dir )
    parser.add_option("-j", "--jar",type="string", dest="jar", metavar="PATH",help="set the LIUM_SpkDiarization jar path (default: %s)" % lium_jar )
    parser.add_option("-b", "--ubm",type="string", dest="ubm", metavar="PATH",help="set the gmm UBM model path (default: %s)" % ubm_path)
    parser.add_option("-u", "--user-interactive", dest="interactive", action="store_true", help="User interactive training")
    parser.add_option("-f", "--output-format", dest="output_format",action="store", type="string", help="output file format [ srt | json | xmp ] (default srt)")

    (options, args) = parser.parse_args()

    if options.keep_intermediate_files:
        keep_intermediate_files = options.keep_intermediate_files
    if options.quiet_mode:
        quiet_mode = options.quiet_mode
    if options.dir_gmm:
        db_dir = options.dir_gmm
    if options.output_format:
        if options.output_format not in ('srt','json','xmp'):
            print 'output format (%s) wrong or not available' % options.output_format
            parser.print_help()
            exit(0)
        output_format = options.output_format
    if options.jar:
        lium_jar = options.jar
    if options.ubm:
        ubm_path = options.ubm      
          
    check_deps()
    if options.file_input:
        extract_speakers(options.file_input,options.interactive,quiet_mode)        
        cmanager.write_output(output_format)
        if not keep_intermediate_files:
            os.remove(cmanager.get_file_basename()+'.seg')            
            os.remove(cmanager.get_file_basename()+'.mfcc')
            w = cmanager.get_file_basename()+'.wav'
            if cmanager.get_filename() != w:
                os.remove(w)
            shutil.rmtree(cmanager.get_file_basename())
        exit(0)
        
    if options.waves_for_gmm and options.speakerid:
        show = None
        waves = options.waves_for_gmm
        speaker = options.speakerid
        w=None
        if len(waves)>1:
            merge_waves(waves[:-1],waves[-1])
            w=waves[-1]
        else:
            w= waves[0]
        basename, extension = os.path.splitext(w)
        show=basename
        build_gmm(show,speaker)
        exit(0)

    parser.print_help()


