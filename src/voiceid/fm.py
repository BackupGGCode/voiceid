#############################################################################
#
# VoiceID, Copyright (C) 2011-2012, Sardegna Ricerche.
# Email: labcontdigit@sardegnaricerche.it, michela.fancello@crs4.it, 
#        mauro.mereu@crs4.it
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
#############################################################################
"""Module containing the low level file manipulation functions."""

import os
import re
import struct
from __init__ import QUIET_MODE, LIUM_JAR, SMS_GMMS, GENDER_GMMS, UBM_PATH, \
    DB_DIR
from utils import start_subprocess, ensure_file_exists, humanize_time


def wave_duration(wavfile):
    """Extract the duration of a wave file in sec.
    
    :type wavfile: string 
    :param wavfile: the wave input file 
    """
    import wave
    w = wave.open(wavfile)
    par = w.getparams()
    w.close()
    return par[3] / par[2]

def merge_waves(input_waves, wavename):
    """Take a list of waves and append them to a brend new destination wave.
     
    :type input_waves: list 
    :param input_waves: the wave files list
    
    :type wavename: string
    :param wavename: the output wave file to be generated
    """
    #if os.path.exists(wavename):
            #raise Exception("File gmm %s already exist!" % wavename)
    waves = [w.replace(" ","\ ") for w in input_waves]
    w = " ".join(waves)
    commandline = "sox " + str(w) + " " + str(wavename)
    start_subprocess(commandline)

def file2wav(filename):
    """Take any kind of video or audio and convert it to a 
    "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, 
    mono 16000 Hz" wave file using gstreamer. If you call it passing a wave it
    checks if in good format, else it converts the wave in the good format.
    
    :type filename: string
    :param filename: the input audio/video file to convert 
    """
    def is_bad_wave(filename):
        """Check if the wave is in correct format for LIUM."""
        import wave
        par = None
        try:
            w = wave.open(filename)
            par = w.getparams()
            w.close()
        except wave.Error,e:
            print e
            return True
        if par[:3] == (1,2,16000) and par[-1:] == ('not compressed',):
            return False
        else:
            return True

    name, ext = os.path.splitext(filename)
    if ext != '.wav' or is_bad_wave(filename):
        start_subprocess( "gst-launch filesrc location='" + filename + "' ! decodebin ! audioresample ! 'audio/x-raw-int,rate=16000' ! audioconvert ! 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1' ! wavenc ! filesink location=" + name + ".wav " )
    ensure_file_exists(name + '.wav')


def merge_gmms(input_files, output_file):
    """Merge two or more gmm files to a single gmm file with more voice models.
    
    :type input_files: list
    :param input_files: the gmm file list to merge
    
    :type output_file: string
    :param output_file: the merged gmm output file
    """
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
    
def get_gender(input_file):
    """Return gender of a given gmm file.
    
    :type input_file: string
    :param input_file: the gmm file
    """
    gmm = open(input_file,'r')

    kind = gmm.read(8)

    num_gmm_string = gmm.read(4)
    num_gmm = struct.unpack('>i', num_gmm_string )

    if num_gmm != (1,):
        print str(num_gmm) + " gmms"
        raise Exception('Loop needed for gmms')

    gmm_1 = gmm.read(8)
    nothing =  gmm.read(4)

    str_len = struct.unpack('>i', gmm.read(4) )
    name = gmm.read(str_len[0])

    gender = gmm.read(1)
    return gender
    
def split_gmm(input_file, output_dir=None):
    """Split a gmm file into gmm files with a single voice model.
    
    :type input_file: string
    :param input_file: the gmm file containing various voice models
    
    :type output_dir: string
    :param output_dir: the directory where is splitted the gmm input file
    """
    def read_gaussian(f):
        g_key = f.read(8)     #read string of 8bytes kind
        if g_key != 'GAUSS___':
            raise Exception("Error: the gaussian is not of GAUSS___ key  (%s)" % g_key)
        g_id = f.read(4)
        g_length = f.read(4)     #readint 4bytes representing the name length
        g_name = f.read( int( struct.unpack('>i', g_length )[0] )  )
        g_gender = f.read(1)
        g_kind = f.read(4)
        g_dim = f.read(4)
        g_count = f.read(4)
        g_weight = f.read(8)

        dimension = int( struct.unpack('>i', g_dim )[0] )

        g_header = g_key + g_id + g_length + g_name + g_gender + g_kind + g_dim + g_count + g_weight

#        data = ''
        datasize = 0
        if g_kind == FULL:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < dimension :
                    datasize += 1
                    t += 1
        else:
            for j in range(dimension) :
                datasize += 1
                t = j
                while t < j+1 :
                    datasize += 1
                    t += 1

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
        h = f.read(4)     #readint 4bytes representing the hash (compatibility)
        l = f.read(4)     #readint 4bytes representing the name length
        #read string of l bytes
        name = f.read( int( struct.unpack('>i',   l )[0] )  ) 
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
            newname = os.path.join(basedir, "%s%04d.gmm" % (filename, index))
        fd = open(newname, 'w')
        fd.write(main_header + f['header'] + f['content'])
        fd.close()
        index += 1
        

def rename_gmm(input_file, identifier):
    """Rename a gmm with a new speaker identifier(name) associated.
    
    :type input_file: string
    :param input_file: the gmm file to rename
    
    :type identifier: string
    :param identifier: the new name or identifier of the gmm model 
    """ 
    
    gmm = open(input_file,'r')
    new_gmm = open(input_file+'.new','w')

    kind = gmm.read(8)
    new_gmm.write(kind)

    num_gmm_string = gmm.read(4) 
    num_gmm = struct.unpack('>i', num_gmm_string )

    if num_gmm != (1,):
        print str(num_gmm) + " gmms"
        raise Exception('Loop needed for gmms')

    new_gmm.write(num_gmm_string)

    gmm_1 = gmm.read(8)
    new_gmm.write(gmm_1)

    nothing =  gmm.read(4) 
    new_gmm.write(nothing)

    str_len = struct.unpack('>i', gmm.read(4) )
    name = gmm.read(str_len[0])
    print name
    new_len = struct.pack('>i', len(identifier) )

    new_gmm.write(new_len)
    new_gmm.write(identifier)

    all_other = gmm.read()

    new_gmm.write(all_other)
    gmm.close()
    new_gmm.close()
    

def build_gmm(filebasename, identifier):
    """Build a gmm (Gaussian Mixture Model) file from a given wave with a 
    speaker identifier  associated.
    
    :type filebasename: string
    :param filebasename: the input file basename
    
    :type identifier: string
    :param identifier: the name or identifier of the speaker
    """

    diarization(filebasename)

    ident_seg(filebasename, identifier)

    extract_mfcc(filebasename)
    
    _train_init(filebasename)

    _train_map(filebasename)

#-------------------------------------
#   seg files and trim functions
#-------------------------------------
def seg2trim(filebasename):
    """Take a wave and splits it in small waves in this directory structure
    <file base name>/<cluster>/<cluster>_<start time>.wav 
    
    :type filebasename: string
    :param filebasename: filebasename of the seg and wav input files
    """
    segfile = filebasename + '.seg'
    s = open(segfile,'r')
    for line in s.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            clust = arr[7]
            st = float(arr[2]) / 100
            end = float(arr[3]) / 100
            try:
                mydir = os.path.join(filebasename, clust)
                os.makedirs( mydir )
            except os.error, e:
                if e.errno == 17:
                    pass
                else:
                    raise os.error
            wave_path = os.path.join(filebasename, clust, 
                                     "%s_%07d.%07d.wav" % (clust, int(st), 
                                                           int(end)))
            commandline = "sox %s.wav %s trim  %s %s" % (filebasename, wave_path, 
                                                         st, end)
            start_subprocess(commandline)
            ensure_file_exists( wave_path )
    s.close()

def seg2srt(segfile):
    """Take a seg file and convert it in a subtitle file (srt).
    
    :type segfile: string
    :param segfile: the segmentation file to convert
    """
    def readtime(aline):
        return int(aline[2])

    basename = os.path.splitext(segfile)[0]
    s = open(segfile,'r')
    lines = []
    for line in s.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            lines.append(arr)
    s.close()

    lines.sort(key=readtime, reverse=False)
    fileoutput = basename+".srt"
    srtfile = open(fileoutput,"w")
    row = 0
    for line in lines:
        row = row + 1
        st = float(line[2]) / 100
        en = st + float(line[3]) / 100
        srtfile.write(str(row) + "\n")
        srtfile.write(humanize_time(st) + " --> " + humanize_time(en) + "\n")
        srtfile.write(line[7] + "\n")
        srtfile.write("\n")

    srtfile.close()
    ensure_file_exists(basename + '.srt')

def extract_mfcc(filebasename):
    """Extract audio features from the wave file, in particular the 
    mel-frequency cepstrum using a sphinx tool.
    
    """
    commandline = "sphinx_fe -verbose no -mswav yes -i %s.wav -o %s.mfcc" %  ( filebasename, filebasename )
    start_subprocess(commandline)
    ensure_file_exists(filebasename + '.mfcc')

def ident_seg(filebasename, identifier):
    """Substitute cluster names with speaker names ang generate a
    "<filebasename>.ident.seg" file."""
    ident_seg_rename(filebasename, identifier, filebasename + '.ident')
 
def ident_seg_rename(filebasename, identifier, outputname):
    """Take a seg file and substitute the clusters with a given name or 
    identifier."""
    f = open(filebasename + '.seg', 'r')
    clusters=[]
    lines = f.readlines()
    for line in lines:
        for k in line.split():
            if k.startswith('cluster:'):
                c = k.split(':')[1]
                clusters.append(c)
    f.close()
    output = open(outputname + '.seg', 'w')
    clusters.reverse()
    for line in lines:
        for c in clusters:
            line = line.replace(c,identifier)
        output.write(line)
    output.close()
    ensure_file_exists(outputname + '.seg')

def srt2subnames(filebasename, key_value):
    """Substitute cluster names with real names in subtitles."""

    def replace_words(text, word_dic):
        """
        take a text and replace words that match a key in a dictionary with
        the associated value, return the changed text
        """
        rc = re.compile('|'.join(map(re.escape, word_dic)))

        def translate(match):
            return word_dic[match.group(0)]+'\n'

        return rc.sub(translate, text)

    file_original_subtitle = open(filebasename + ".srt")
    original_subtitle = file_original_subtitle.read()
    file_original_subtitle.close()
    key_value = dict(map(lambda (key, value): (str(key) + "\n", value), 
                         key_value.items()))
    text = replace_words(original_subtitle, key_value)
    out_file = filebasename + ".ident.srt"
    # create a output file
    fout = open(out_file, "w")
    fout.write(text)
    fout.close()
    ensure_file_exists(out_file)

def file2trim(filename):
    """Take a video or audio file and converts it into smaller waves according
    to the diarization process.
    
    :type filename: string
    :param filename: the input file audio/video 
    """
    if not QUIET_MODE: 
        print "*** converting video to wav ***"
    file2wav(filename)
    file_basename = os.path.splitext(filename)[0]
    if not QUIET_MODE: 
        print "*** diarization ***"
    diarization(file_basename)
    if not QUIET_MODE: 
        print "*** trim ***"
    seg2trim(file_basename)

#--------------------------------------------
#   diarization and voice matching functions
#--------------------------------------------
def _silence_segmentation(filebasename):
    """Make a basic segmentation file for the wave file, cutting off the silence.""" 
    start_subprocess( 'java -Xmx2024m -cp '+LIUM_JAR+' fr.lium.spkDiarization.programs.MSegInit --fInputMask=%s.mfcc --fInputDesc=audio16kHz2sphinx,1:1:0:0:0:0,13,0:0:0 --sInputMask= --sOutputMask=%s.s.seg ' +  filebasename )
    ensure_file_exists(filebasename+'.s.seg')
    
def _gender_detection(filebasename):
    """Build a segmentation file where for every segment is identified the gender of the voice."""
    start_subprocess( 'java -Xmx2024m -cp '+LIUM_JAR+' fr.lium.spkDiarization.programs.MDecode  --fInputMask=%s.wav --fInputDesc=audio2sphinx,1:3:2:0:0:0,13,0:0:0 --sInputMask=%s.s.seg --sOutputMask=%s.g.seg --dPenality=10,10,50 --tInputMask=' + SMS_GMMS + ' ' + filebasename )
    ensure_file_exists(filebasename+'.g.seg')
    cmd = 'java -Xmx2024m -cp '+LIUM_JAR+' fr.lium.spkDiarization.programs.MScore --help  --sGender --sByCluster --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:0:0 --fInputMask=%s.mfcc --sInputMask=%s.g.seg --sOutputMask=%s.seg --tInputMask=' + GENDER_GMMS + ' ' + filebasename
    start_subprocess( cmd )
    ensure_file_exists(filebasename+'.seg')

def diarization(filebasename):
    """Take a wave file in the correct format and build a segmentation file. 
    The seg file shows how much speakers are in the audio and when they talk.
    
    :type filebasename: string
    :param filebasename: the basename of the wav file to process
    """
    start_subprocess( 'java -Xmx2024m -jar '+LIUM_JAR+' --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering ' +  filebasename )
    ensure_file_exists(filebasename+'.seg')

def _train_init(filebasename):
    """Train the initial speaker gmm model."""
    commandline = 'java -Xmx256m -cp '+LIUM_JAR+' fr.lium.spkDiarization.programs.MTrainInit --sInputMask=%s.ident.seg --fInputMask=%s.wav --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4 --emInitMethod=copy --tInputMask=' + UBM_PATH + ' --tOutputMask=%s.init.gmm ' + filebasename
    start_subprocess(commandline)
    ensure_file_exists(filebasename+'.init.gmm')

def _train_map(filebasename):
    """Train the speaker model using a MAP adaptation method."""
    commandline = 'java -Xmx256m -cp '+LIUM_JAR+' fr.lium.spkDiarization.programs.MTrainMAP --sInputMask=%s.ident.seg --fInputMask=%s.mfcc --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4 --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm ' + filebasename 
    start_subprocess(commandline)
    ensure_file_exists(filebasename+'.gmm')

def mfcc_vs_gmm(filebasename, gmm_file, gender, custom_db_dir=None):
    """Match a mfcc file and a given gmm model file and produce a segmentation file containing the score obtained. 
    
    :type filebasename: string
    :param filebasename: the basename of the mfcc file to process
    
    :type gmm_file: string
    :param gmm_file: the path of the gmm file containing the voice model
    
    :type gender: char
    :param gender: F, M or U, the gender of the voice model
    
    :type custom_db_dir: None or string
    :param custom_db_dir: the voice models database to use 
    """
    database = DB_DIR
    if custom_db_dir != None:
        database = custom_db_dir
    gmm_name = os.path.split(gmm_file)[1]
    commandline = 'java -Xmx256M -cp ' + LIUM_JAR + ' fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg --fInputMask=%s.mfcc --sOutputMask=%s.ident.' + gender + '.' + gmm_name + '.seg --sOutputFormat=seg,UTF8  --fInputDesc=audio16kHz2sphinx,1:3:2:0:0:0,13,1:0:300:4 --tInputMask=' + database + '/' + gender + '/' + gmm_file + ' --sTop=8,' + UBM_PATH + '  --sSetLabel=add --sByCluster ' + filebasename 
    start_subprocess(commandline)
    ensure_file_exists(filebasename + '.ident.' + gender + '.' + gmm_name + '.seg')
    
#def threshold_tuning():
#    """ Get a score to tune up the threshold to define when a speaker is unknown"""
#    filebasename = os.path.join(test_path,'mr_arkadin')
#    gmm_file = "mrarkadin.gmm"
#    gender = 'M'
#    ensure_file_exists(filebasename+'.wav')
#    ensure_file_exists( os.path.join(test_path,gender,gmm_file ) )
#    file2trim(filebasename+'.wav')
#    extract_mfcc(filebasename)
#    mfcc_vs_gmm(filebasename, gmm_file, gender,custom_db_dir=test_path)
#    clusters = {}
#    extract_clusters(filebasename+'.seg',clusters)
#    manage_ident(filebasename,gender+'.'+gmm,clusters)
#    return clusters['S0'].speakers['mrarkadin']
