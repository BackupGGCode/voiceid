# -*- coding: utf-8 -*-
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
from . import VConf, utils

CONFIGURATION = VConf()

JAVA_MEM = '2048'
JAVA_EXE = 'java'
import sys
if sys.platform == 'win32':
    JAVA_MEM = '1024'
    JAVA_EXE = 'javaw'


def wave_duration(wavfile):
    """Extract the duration of a wave file in sec.

    :type wavfile: string
    :param wavfile: the wave input file"""
    import wave
    w_file = wave.open(wavfile)
    par = w_file.getparams()
    w_file.close()
    return par[3] / par[2]


def merge_waves(input_waves, wavename):
    """Take a list of waves and append them to a brend new destination wave.

    :type input_waves: list
    :param input_waves: the wave files list

    :type wavename: string
    :param wavename: the output wave file to be generated"""
    #if os.path.exists(wavename):
            #raise Exception("File gmm %s already exist!" % wavename)
    waves = [w_names.replace(" ", "\ ") for w_names in input_waves]
    w_names = " ".join(waves)
    commandline = "sox " + str(w_names) + " " + str(wavename)
    
    utils.start_subprocess(commandline)


def file2wav(filename):
    """Take any kind of video or audio and convert it to a
    "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit,
    mono 16000 Hz" wave file using gstreamer. If you call it passing a wave it
    checks if in good format, else it converts the wave in the good format.

    :type filename: string
    :param filename: the input audio/video file to convert"""
    name, ext = os.path.splitext(filename)
    if ext == '.wav' and utils.is_good_wave(filename):
        pass
    else:
        if ext == '.wav':
            name += '_'
        utils.start_subprocess("gst-launch filesrc location='" + filename
           + "' ! decodebin ! audioresample ! 'audio/x-raw-int,rate=16000' !"
           + " audioconvert !"
           + " 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1' !"
           + "wavenc ! filesink location=" + name + ".wav ")
    utils.ensure_file_exists(name + '.wav')
    return name + ext


def merge_gmms(input_files, output_file):
    """Merge two or more gmm files to a single gmm file with more voice models.

    :type input_files: list
    :param input_files: the gmm file list to merge

    :type output_file: string
    :param output_file: the merged gmm output file"""
    num_gmm = 0
    gmms = ''
    for ifile in input_files:
        try:
            current_f = open(ifile, 'rb')
        except (IOError, OSError):
            continue
        kind = current_f.read(8)
        if kind != 'GMMVECT_':
            raise Exception('different kinds of models!')
        
        line = current_f.read(4)
        num = struct.unpack('>i', line)
        num_gmm += int(num[0])
        byte = current_f.read(1)
        all_other = ""
        
        while byte:
            # Do stuff with byte.
            all_other += byte
            byte = current_f.read(1)
            
        gmms += all_other
        current_f.close()

    num_gmm_string = struct.pack('>i', num_gmm)
    new_gmm = open(output_file, 'w')
    new_gmm.write("GMMVECT_")
    new_gmm.write(num_gmm_string)
    new_gmm.write(gmms)

    new_gmm.close()


def get_gender(input_file):
    """Return gender of a given gmm file.

    :type input_file: string
    :param input_file: the gmm file
    """
    gmm = open(input_file, 'rb')
    gmm.read(8)  # kind
    num_gmm_string = gmm.read(4)
    num_gmm = struct.unpack('>i', num_gmm_string)

    if num_gmm != (1,):
        raise Exception('Loop needed for gmms')

    gmm.read(8)  # gmm_1
    gmm.read(4)  # nothing

    str_len = struct.unpack('>i', gmm.read(4))
    gmm.read(str_len[0]) # name

    gender = gmm.read(1)
    return gender


def _read_gaussian(g_file):
    """Read a gaussian in binary format"""
    full = 0
    g_key = g_file.read(8)     # read string of 8bytes kind
    if g_key != 'GAUSS___':
        raise Exception("Error: the gaussian is not"
                        + " of GAUSS___ key  (%s)" % g_key)
    g_id = g_file.read(4)
    g_length = g_file.read(4)  # readint 4bytes representing the name len
    g_name = g_file.read(int(struct.unpack('>i', g_length)[0]))
    g_gender = g_file.read(1)
    g_kind = g_file.read(4)
    g_dim = g_file.read(4)
    g_count = g_file.read(4)
    g_weight = g_file.read(8)
    dimension = int(struct.unpack('>i', g_dim)[0])
    g_header = g_key + g_id + g_length + g_name + g_gender + g_kind + g_dim
    g_header = g_header + g_count + g_weight
    datasize = 0
    if g_kind == full:
        for jay in range(dimension) :
            datasize += 1
            tee = jay
            while tee < dimension :
                datasize += 1
                tee += 1
    else:
        for jay in range(dimension) :
            datasize += 1
            tee = jay
            while tee < jay + 1 :
                datasize += 1
                tee += 1
    return g_header + g_file.read(datasize * 8)


def _read_gaussian_container(g_file):
    """Read a gaussian container in a binary format"""
    # gaussian container
    chk = g_file.read(8)   # read string of 8bytes
    if chk != "GAUSSVEC":
        raise Exception("Error: the gaussian container" +
                        " is not of GAUSSVEC kind %s" % chk)
    gcs = g_file.read(4)   # readint 4bytes representing the size of
    # the gaussian container
    stuff = chk + gcs
    for index in range(int(struct.unpack('>i', gcs)[0])):
        stuff += _read_gaussian(g_file)
    return stuff


def _read_gmm(g_file):
    """Read a gmm in a binary format"""
    myfile = {}
    # single gmm
    kind = g_file.read(8)     # read string of 8bytes kind
    if kind != "GMM_____":
        raise Exception("Error: Gmm section doesn't match GMM_____ kind")
    hash_ = g_file.read(4)  # readint 4bytes representing the hash (compatib)
    length = g_file.read(4)  # readint 4bytes representing the name length
    # read string of length bytes
    name = g_file.read(int(struct.unpack('>i', length)[0]))
    myfile['name'] = name
    gen = g_file.read(1)     # read a char representing the gender
    gaussk = g_file.read(4) # readint 4bytes representing the gaussian kind
    dim = g_file.read(4)   # readint 4bytes representing the dimension
    comp = g_file.read(4)  # readint 4bytes representing the number of comp
    gvect_header = kind + hash_ + length + name + gen + gaussk + dim + comp
    myfile['header'] = gvect_header
    myfile['content'] = _read_gaussian_container(g_file)
    return myfile


def split_gmm(input_file, output_dir=None):
    """Split a gmm file into gmm files with a single voice model.

    :type input_file: string
    :param input_file: the gmm file containing various voice models

    :type output_dir: string
    :param output_dir: the directory where is splitted the gmm input file"""


    g_file = open(input_file, 'rb')
    key = g_file.read(8)
    if key != 'GMMVECT_':  # gmm container
        raise Exception('Error: Not a GMMVECT_ file!')

    size = g_file.read(4)
    num = int(struct.unpack('>i', size)[0])  # number of gmms
    main_header = key + struct.pack('>i', 1)
    files = []
    for num in range(num):
        files.append(_read_gmm(g_file))
    g_file.close()
    file_basename = input_file[:-4]
    index = 0
    basedir, filename = os.path.split(file_basename)
    if output_dir != None:
        basedir = output_dir
        for g_file in files:
            newname = os.path.join(basedir, "%s%04d.gmm" % (filename, index))
            gmm_f = open(newname, 'w')
            gmm_f.write(main_header + g_file['header'] + g_file['content'])
            gmm_f.close()
            index += 1


def rename_gmm(input_file, identifier):
    """Rename a gmm with a new speaker identifier(name) associated.

    :type input_file: string
    :param input_file: the gmm file to rename

    :type identifier: string
    :param identifier: the new name or identifier of the gmm model"""
    gmm = open(input_file, 'rb')
    new_gmm = open(input_file + '.new', 'w')
    kind = gmm.read(8)
    new_gmm.write(kind)
    num_gmm_string = gmm.read(4)
    num_gmm = struct.unpack('>i', num_gmm_string)
    if num_gmm != (1,):
        raise Exception('Loop needed for gmms')
    new_gmm.write(num_gmm_string)
    gmm_1 = gmm.read(8)
    new_gmm.write(gmm_1)
    nothing = gmm.read(4)
    new_gmm.write(nothing)
    str_len = struct.unpack('>i', gmm.read(4))
    name = gmm.read(str_len[0])
    new_len = struct.pack('>i', len(identifier))
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
    :param identifier: the name or identifier of the speaker"""
    if sys.platform == 'win32':
        diarization(filebasename)
        
        if os.path.exists(filebasename+'.g.3.seg'):
            os.remove(filebasename+'.seg')
            os.rename(filebasename+'.g.3.seg', filebasename+'.seg')
        if sys.platform == 'win32':
            import fileinput
            for line in fileinput.FileInput(filebasename+'.seg',inplace=0):
                line = line.replace("\\\\","/")
    else:
        diarization_standard(filebasename)
        
                         
    ident_seg(filebasename, identifier)
    _train_init(filebasename)
    _train_map(filebasename)
    

#-------------------------------------
#   seg files and trim functions
#-------------------------------------
def seg2trim(filebasename):
    """Take a wave and splits it in small waves in this directory structure
    <file base name>/<cluster>/<cluster>_<start time>.wav

    :type filebasename: string
    :param filebasename: filebasename of the seg and wav input files"""
    segfile = filebasename + '.seg'
    seg = open(segfile, 'r')
    for line in seg.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            clust = arr[7]
            start = float(arr[2]) / 100
            end = float(arr[3]) / 100
            try:
                mydir = os.path.join(filebasename, clust)
                if sys.platform == 'win32':
                    mydir = filebasename +'/'+ clust
                os.makedirs(mydir)
            except os.error, err:
                if err.errno == 17:
                    pass
                else:
                    raise os.error
            wave_path = os.path.join(filebasename, clust,
                                     "%s_%07d.%07d.wav" % (clust, int(start),
                                                           int(end)))
            
            if sys.platform == 'win32':
                wave_path = filebasename +"/"+ clust +"/"+ "%s_%07d.%07d.wav" % (clust, int(start), int(end))
            
            commandline = "sox %s.wav %s trim  %s %s" % (filebasename,
                                                         wave_path,
                                                         start, end)    
                        
            utils.start_subprocess(commandline)
            utils.ensure_file_exists(wave_path)
    seg.close()


def seg2srt(segfile):
    """Take a seg file and convert it in a subtitle file (srt).

    :type segfile: string
    :param segfile: the segmentation file to convert"""
    def readtime(aline):
        "Help function for sort, to extract time from line"
        return int(aline[2])

    basename = os.path.splitext(segfile)[0]
    seg = open(segfile, 'r')
    lines = []
    for line in seg.readlines():
        if not line.startswith(";;"):
            arr = line.split()
            lines.append(arr)
    seg.close()
    lines.sort(key=readtime, reverse=False)
    fileoutput = basename + ".srt"
    srtfile = open(fileoutput, "w")
    row = 0
    for line in lines:
        row = row + 1
        start = float(line[2]) / 100
        end = start + float(line[3]) / 100
        srtfile.write(str(row) + "\n")
        srtfile.write(utils.humanize_time(start) + " --> "
                      + utils.humanize_time(end) + "\n")
        srtfile.write(line[7] + "\n")
        srtfile.write("\n")
    srtfile.close()
    utils.ensure_file_exists(basename + '.srt')


def ident_seg(filebasename, identifier):
    """Substitute cluster names with speaker names ang generate a
    "<filebasename>.ident.seg" file."""
    ident_seg_rename(filebasename, identifier, filebasename + '.ident')


def ident_seg_rename(filebasename, identifier, outputname):
    """Take a seg file and substitute the clusters with a given name or
    identifier."""
    seg_f = open(filebasename + '.seg', 'r')
    clusters = []
    lines = seg_f.readlines()
    for line in lines:
        for key in line.split():
            if key.startswith('cluster:'):
                clu = key.split(':')[1]
                clusters.append(clu)
    seg_f.close()
    output = open(outputname + '.seg', 'w')
    clusters.reverse()
    for line in lines:
        for clu in clusters:
            line = line.replace(clu, identifier)
        output.write(line)
    output.close()
    utils.ensure_file_exists(outputname + '.seg')


def srt2subnames(filebasename, key_value):
    """Substitute cluster names with real names in subtitles."""

    def replace_words(text, word_dic):
        """Take a text and replace words that match a key in a dictionary with
        the associated value, return the changed text"""
        rec = re.compile('|'.join(map(re.escape, word_dic)))

        def translate(match):
            "not documented"
            return word_dic[match.group(0)] + '\n'

        return rec.sub(translate, text)

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
    utils.ensure_file_exists(out_file)


def file2trim(filename):
    """Take a video or audio file and converts it into smaller waves according
    to the diarization process.

    :type filename: string
    :param filename: the input file audio/video"""
    if not CONFIGURATION.QUIET_MODE:
        print "*** converting video to wav ***"
    file2wav(filename)
    file_basename = os.path.splitext(filename)[0]
    if not CONFIGURATION.QUIET_MODE:
        print "*** diarization ***"
    diarization(file_basename)
    if not CONFIGURATION.QUIET_MODE:
        print "*** trim ***"
    seg2trim(file_basename)


#--------------------------------------------
#   diarization and voice matching functions
#--------------------------------------------



def _silence_segmentation(filebasename):
    """Make a basic segmentation file for the wave file,
    cutting off the silence."""
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -cp '
            + CONFIGURATION.LIUM_JAR
            + ' fr.lium.spkDiarization.programs.MSegInit '
            + '--fInputMask=%s.wav '
            + '--fInputDesc=audio2sphinx,1:1:0:0:0:0,13,0:0:0'
            + ' --sInputMask= --sOutputMask=%s.s.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.s.seg')


def _gender_detection(filebasename):
    """Build a segmentation file where for every segment is identified
    the gender of the voice."""
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -cp '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MDecode  '
           + '--fInputMask=%s.wav '
           + '--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,0:0:0 '
           + '--sInputMask=%s.s.seg --sOutputMask=%s.g.seg '
           + '--dPenality=10,10,50 --tInputMask=' + CONFIGURATION.SMS_GMMS
           + ' ' + filebasename)
    utils.ensure_file_exists(filebasename + '.g.seg')
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -cp '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MScore --help  --sGender '
           + '--sByCluster '
           + '--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:1:0:0 '
           + '--fInputMask=%s.wav --sInputMask=%s.g.seg --sOutputMask=%s.seg '
           + '--tInputMask=' + CONFIGURATION.GENDER_GMMS + ' ' + filebasename)
    utils.ensure_file_exists(filebasename + '.seg')


def diarization_standard(filebasename):
    """Take a wave file in the correct format and build a segmentation file.
    The seg file shows how much speakers are in the audio and when they talk.

    :type filebasename: string
    :param filebasename: the basename of the wav file to process"""
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -jar '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.system.Diarization '
           + '--fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering '
           + filebasename)
    utils.ensure_file_exists(filebasename + '.seg')


def diarization(filebasename, h_par='3', c_par='1.5'):
    """Take a wav and wave file in the correct format and build a
    segmentation file.
    The seg file shows how much speakers are in the audio and when they talk.

    :type filebasename: string
    :param filebasename: the basename of the wav file to process"""
#    par=' --help --trace '
    par = ''
    #generate_uem_seg(filebasename)
    st_fdesc = "audio2sphinx,1:1:0:0:0:0,13,0:0:0"
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MSegInit  '
           + par + ' --fInputMask=%s.wav --fInputDesc='
           + st_fdesc + ' '
           + ' --sOutputMask=%s.i.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.i.seg')

    #Speech/Music/Silence segmentation
    md_fdesk = 'audio2sphinx,1:3:2:0:0:0,13,0:0:0'
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MDecode  '
           + par + '  --fInputMask=%s.wav  --fInputDesc='
           + md_fdesk + ' --sInputMask=%s.i.seg     --tInputMask='
           + CONFIGURATION.SMS_GMMS
           + ' --dPenality=10,10,50  --sOutputMask=%s.pms.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.pms.seg')

    #GLR based segmentation, make small segments
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR + ' fr.lium.spkDiarization.programs.MSeg  '
           + par + ' --fInputMask=%s.wav --fInputDesc=' + st_fdesc
           + '    --sInputMask=%s.i.seg  '
           + ' --kind=FULL --sMethod=GLR --sOutputMask=%s.s.seg '
           + filebasename)
    utils.ensure_file_exists(filebasename + '.s.seg')

    # linear clustering
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MClust ' + par
           + ' --fInputMask=%s.wav --fInputSpeechThr=0.1 --fInputDesc=' + st_fdesc
           + ' --sInputMask=%s.s.seg --cMethod=l --cThr=2 '
           + '--sOutputMask=%s.l.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.l.seg')

    # hierarchical clustering
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MClust ' + par
           + ' --fInputMask=%s.wav --fInputDesc=' + st_fdesc
           + ' --sInputMask=%s.l.seg --cMethod=h --cThr=' + h_par
           + '  --sOutputMask=%s.h.' + h_par + '.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.h.' + h_par + '.seg')

    # initialize GMM
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MTrainInit '
           + par + ' --fInputMask=%s.wav --fInputDesc='
           + st_fdesc + '    --sInputMask=%s.h.' + h_par
           + '.seg --nbComp=8 --kind=DIAG    --tOutputMask=%s.init.gmms '
           + filebasename)
    utils.ensure_file_exists(filebasename + '.init.gmms')

    # EM computation
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MTrainEM ' + par
           + ' --fInputMask=%s.wav --fInputDesc=' + st_fdesc
           + ' --sInputMask=%s.h.' + h_par
           + '.seg --tInputMask=%s.init.gmms --nbComp=8 '
           + '--kind=DIAG --tOutputMask=%s.gmms ' + filebasename)
    utils.ensure_file_exists(filebasename + '.gmms')

    #Viterbi decoding
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MDecode '
           + par + ' --fInputMask=%s.wav  --fInputDesc='
           + st_fdesc + ' --sInputMask=%s.h.' + h_par
           + '.seg  --tInputMask=%s.gmms --dPenality=250'
           + '  --sOutputMask=%s.d.' + h_par + '.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.d.' + h_par + '.seg')

    #Adjust segment boundaries
    s_desc = 'audio2sphinx,1:1:0:0:0:0,13,0:0:0'
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR + ' fr.lium.spkDiarization.tools.SAdjSeg '
           + par + '  --fInputMask=%s.wav  --fInputDesc=' + s_desc
           + '    --sInputMask=%s.d.' + h_par + '.seg   --sOutputMask=%s.adj.'
           + h_par + '.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.adj.' + h_par + '.seg')

    #filter spk segmentation according pms segmentation
    fl_desc = 'audio2sphinx,1:3:2:0:0:0,13,0:0:0'
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR + ' fr.lium.spkDiarization.tools.SFilter '
           + par + '  --fInputMask=%s.wav  --fInputDesc=' + fl_desc
           + '   --sInputMask=%s.adj.' + h_par
           + '.seg  --fltSegMinLenSpeech=150 --fltSegMinLenSil=25 '
           + '--sFilterClusterName=j --fltSegPadding=25 '
           + '--sFilterMask=%s.pms.seg --sOutputMask=%s.flt.'
           + h_par + '.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.flt.' + h_par + '.seg')

    #Split segment longer than 20s
    ss_desc = 'audio2sphinx,1:3:2:0:0:0,13,0:0:0'
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR + ' fr.lium.spkDiarization.tools.SSplitSeg '
           + par + '  --fInputMask=%s.wav  --fInputDesc=' + ss_desc
           + ' --sInputMask=%s.flt.' + h_par + '.seg  --tInputMask='
           + CONFIGURATION.S_GMMS + ' --sFilterMask=%s.pms.seg '
           + '--sFilterClusterName=iS,iT,j  --sOutputMask=%s.spl.' + h_par
           + '.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.spl.' + h_par + '.seg')

    #Set gender and bandwith
    f_desc_clr = "audio2sphinx,1:3:2:0:0:0,13,1:1:300:4"
    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR + ' fr.lium.spkDiarization.programs.MScore '
           + par + ' --fInputMask=%s.wav --fInputDesc=' + f_desc_clr
           + ' --sInputMask=%s.spl.' + h_par + '.seg --tInputMask='
           + CONFIGURATION.GENDER_GMMS
           + ' --sGender --sByCluster --sOutputMask=%s.g.'
           + h_par + '.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.g.' + h_par + '.seg')

    utils.start_subprocess(JAVA_EXE +' -Xmx' + JAVA_MEM + 'm -classpath '
           + CONFIGURATION.LIUM_JAR
           + ' fr.lium.spkDiarization.programs.MClust ' + par
           + ' --fInputMask=%s.wav --fInputDesc=' + f_desc_clr
           + ' --sInputMask=%s.g.' + h_par + '.seg   –fInputSpeechThr=1 --tInputMask='
           + CONFIGURATION.UBM_PATH + ' --cMethod=ce --cThr=' + c_par
           + ' --emCtrl=1,5,0.01 --sTop=5,'
           + CONFIGURATION.UBM_PATH
           + ' --tOutputMask=%s.c.gmm --sOutputMask=%s.seg ' + filebasename)
    utils.ensure_file_exists(filebasename + '.seg')

    if not CONFIGURATION.KEEP_INTERMEDIATE_FILES:
        f_list = ['.i.seg', '.pms.seg', '.s.seg', '.l.seg',
                  '.h.' + h_par + '.seg', '.init.gmms', '.gmms',
                  '.d.' + h_par + '.seg', '.adj.' + h_par + '.seg',
                  '.flt.' + h_par + '.seg', '.spl.' + h_par + '.seg',
                  '.g.' + h_par + '.seg']
        for ext in f_list:
            os.remove(filebasename + ext)


def _train_init(filebasename):
    """Train the initial speaker gmm model."""
    utils.start_subprocess(JAVA_EXE +' -Xmx256m -cp ' + CONFIGURATION.LIUM_JAR
        + ' fr.lium.spkDiarization.programs.MTrainInit '
        + '--sInputMask=%s.ident.seg --fInputMask=%s.wav '
        + '--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:1:300:4 '
        + '--emInitMethod=copy --tInputMask=' + CONFIGURATION.UBM_PATH
        + ' --tOutputMask=%s.init.gmm ' + filebasename)
    utils.ensure_file_exists(filebasename + '.init.gmm')


def _train_map(filebasename):
    """Train the speaker model using a MAP adaptation method."""
    utils.start_subprocess(JAVA_EXE +' -Xmx256m -cp ' + CONFIGURATION.LIUM_JAR
        + ' fr.lium.spkDiarization.programs.MTrainMAP --sInputMask=%s.ident.seg'
        + ' --fInputMask=%s.wav '
        + '--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:1:300:4 '
        + '--tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 '
        + '--tOutputMask=%s.gmm ' + filebasename)
    
    utils.ensure_file_exists(filebasename + '.gmm')


def wav_vs_gmm(filebasename, gmm_file, gender, custom_db_dir=None):
    """Match a wav file and a given gmm model file and produce a segmentation
    file containing the score obtained.

    :type filebasename: string
    :param filebasename: the basename of the wav file to process

    :type gmm_file: string
    :param gmm_file: the path of the gmm file containing the voice model

    :type gender: char
    :param gender: F, M or U, the gender of the voice model

    :type custom_db_dir: None or string
    :param custom_db_dir: the voice models database to use"""
    database = CONFIGURATION.DB_DIR
    
    if custom_db_dir != None:
        database = custom_db_dir
    gmm_name = os.path.split(gmm_file)[1]
    if sys.platform == 'win32':
        utils.start_subprocess(JAVA_EXE +' -Xmx256M -cp ' + CONFIGURATION.LIUM_JAR
        + ' fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg '
        + '--fInputMask=%s.wav --sOutputMask=%s.ident.' + gender + '.'
        + gmm_name + '.seg --sOutputFormat=seg,UTF8 '
        + '--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:0:300:4 '
        + '--tInputMask=' + database + '\\' + gender + '\\' + gmm_file
        + ' --sTop=8,' + CONFIGURATION.UBM_PATH
        + '  --sSetLabel=add --sByCluster ' + filebasename)
    else:
        utils.start_subprocess(JAVA_EXE +' -Xmx256M -cp ' + CONFIGURATION.LIUM_JAR
        + ' fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg '
        + '--fInputMask=%s.wav --sOutputMask=%s.ident.' + gender + '.'
        + gmm_name + '.seg --sOutputFormat=seg,UTF8 '
        + '--fInputDesc=audio2sphinx,1:3:2:0:0:0,13,1:0:300:4 '
        + '--tInputMask=' + database + '/' + gender + '/' + gmm_file
        + ' --sTop=8,' + CONFIGURATION.UBM_PATH
        + '  --sSetLabel=add --sByCluster ' + filebasename)
    utils.ensure_file_exists(filebasename + '.ident.'
                             + gender + '.' + gmm_name + '.seg')
    
#     f = open(filebasename + '.ident.'
#                              + gender + '.' + gmm_name + '.seg', "r")
#     print "SEG CREATED "+filebasename + '.ident.' + gender + '.' + gmm_name + '.seg'
#     print f.readlines()
#     f.close() 
#     print "END SEG"



#def threshold_tuning():
#    """ Get a score to tune up the 
#    threshold to define when a speaker is unknown"""
#    filebasename = os.path.join(test_path,'mr_arkadin')
#    gmm_file = "mrarkadin.gmm"
#    gender = 'M'
#    utils.ensure_file_exists(filebasename+'.wav')
#    utils.ensure_file_exists( os.path.join(test_path,gender,gmm_file ) )
#    file2trim(filebasename+'.wav')
#    extract_mfcc(filebasename)
#    wav_vs_gmm(filebasename, gmm_file, gender,custom_db_dir=test_path)
#    clusters = {}
#    extract_clusters(filebasename+'.seg',clusters)
#    manage_ident(filebasename,gender+'.'+gmm,clusters)
#    return clusters['S0'].speakers['mrarkadin']