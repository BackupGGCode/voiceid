#!/usr/bin/env python 
from optparse import OptionParser
from multiprocessing import Process, cpu_count, active_children
import os
import shlex, subprocess
import sys, signal
import time
import re
import string
import tempfile
p = None
verbose = False

lium_jar='./LIUM_SpkDiarization.jar'
db_dir = './gmm_db'
keep_intermediate_files = False

dev_null = open('/dev/null','w')

if verbose:
	dev_null = None

def start_subprocess(commandline):
	""" Starts a subprocess using the given commandline and check for correct termination """
	args = shlex.split(commandline)
	p = subprocess.Popen(args, stdout=dev_null, stderr=dev_null)
	retval = p.wait()
	if retval != 0: 
		raise Exception("Subprocess closed unexpectedly "+str(p) )

def ensure_file_exists(filename):
	""" Ensure file exists and not empty """
	if not os.path.exists(filename):
		raise Exception("File %s not correctly created"  % filename)
	if not (os.path.getsize(filename) > 0):
		raise Exception("File %s empty"  % filename)

def  check_deps():
	""" Check for dependency """
	import magic
	ensure_file_exists(lium_jar)
	if not os.path.exists(db_dir):
		raise Exception("No gmm db directory found in %s (take a look to the configuration, db_dir parameter)" % db_dir )
	elif os.listdir(db_dir) == []:
		raise Exception("Gmm db directory found in %s is empty" % db_dir )
		

def humanize_time(secs):
	""" Convert seconds into time format """
	mins, secs = divmod(secs, 60)
	hours, mins = divmod(mins, 60)
	return '%02d:%02d:%02d,%s' % (hours, mins, int(secs), str(("%0.3f" % secs ))[-3:] )

def video2wav(show):
	""" Takes any kind of video or audio and convert it to a "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz" wave file using gstreamer. If you call it passing a wave it checks if in good format, otherwise it converts the wave in the good format """
	def is_bad_wave(show):
		import magic
		ms = magic.open(magic.MAGIC_NONE)
		ms.load()
		info =  ms.file(show)
		if info == "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz":
			return False
		else:
			return True

	name, ext = os.path.splitext(show)
	if ext != '.wav' or is_bad_wave(show):
		start_subprocess( "gst-launch-0.10 filesrc location='"+show+"' ! decodebin ! audioresample ! 'audio/x-raw-int,rate=16000' ! audioconvert ! 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1' ! wavenc ! filesink location="+name+".wav " )
	ensure_file_exists(name+'.wav')


def diarization(showname):
	""" Takes a wave file in the correct format and build a segmentation file. The seg file shows how much speakers are in the audio and when they talk """
	start_subprocess( 'java -Xmx2024m -jar '+lium_jar+'   --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering ' +  showname )
	ensure_file_exists(showname+'.seg')

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
				os.makedirs("%s/%s" % (basename, clust) )
			except os.error as e:
				if e.errno == 17:
					pass
				else:
					raise os.error
			commandline = "sox %s.wav %s/%s/%s_%s.wav trim  %s %s" % ( basename, basename, clust, clust, st, st, end )
			start_subprocess(commandline)
			ensure_file_exists( "%s/%s/%s_%s.wav" % (basename, clust, clust, st) )
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
		srtfile.write(str(row)+"\n")
		srtfile.write(humanize_time(float(line[2])) + " --> " + humanize_time(float(line[2])+float(line[3]))+"\n")
		srtfile.write(line[7]+"\n")
		srtfile.write(""+"\n")
			
	srtfile.close()
	ensure_file_exists(basename+'.srt')

def video2trim(videofile):
	""" Takes a video or audio file and converts it into smaller waves according to the diarization process """
	print "*** converting video to wav ***"
	video2wav(videofile)
	show, ext = os.path.splitext(videofile)
	print "*** diarization ***"
	diarization(show)
	print "*** trim ***"
	seg2trim(show+'.seg')

def extract_mfcc(show):
	""" Extract audio features from the wave file, in particular the mel-frequency cepstrum using a sphinx tool """
	commandline = "sphinx_fe -verbose no -mswav yes -i %s.wav -o %s.mfcc" %  ( show, show )
	start_subprocess(commandline)
	ensure_file_exists(show+'.mfcc')

def ident_seg(showname,name):
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
	output = open(showname+'.ident.seg', 'w')
	clusters.reverse()
	for line in lines:
		for c in clusters:
			line.replace(c,name)
		output.write(line+'\n')
	output.close()
	ensure_file_exists(showname+'.ident.seg')

def train_init(show):
	commandline = 'java -Xmx2024m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=%s.ident.seg --fInputMask=%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=./ubm.gmm --tOutputMask=%s.init.gmm '+show
	start_subprocess(commandline)
	ensure_file_exists(show+'.init.gmm')

def train_map(show):
	commandline = 'java -Xmx2024m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=%s.ident.seg --fInputMask=%s.mfcc --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm ' + show 
	start_subprocess(commandline)
	ensure_file_exists(show+'.gmm')

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
	key_value=dict(map(lambda (key, value): (str(key)+"\n", value), key_value.items()))
	text = replace_words(original_subtitle, key_value)
	out_file = showname+"_new.srt"
	# create a output file
	fout = open(out_file, "w")
	fout.write(text)
	fout.close()	
	ensure_file_exists(out_file)

def extract_clusters(filename, clusters):
	""" Read clusters from segmentation file """
	f = open(filename,"r")
	for l in f:
		 if l.startswith(";;") :
			ll = l.split()[1].split(':')[1]	
			clusters[ll] = {}
	f.close()

def mfcc_vs_gmm(showname, gmm):
	""" Match a mfcc file and a given gmm model file """
	commandline = 'java -Xmx2G -Xms2G -cp '+lium_jar+'  fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg   --fInputMask=%s.mfcc  --sOutputMask=%s.ident.'+gmm+'.seg --sOutputFormat=seg,UTF8  --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:0:300:4" --tInputMask='+db_dir+'/'+gmm+' --sTop=8,ubm.gmm  --sSetLabel=add --sByCluster '+  showname 
	start_subprocess(commandline)
	ensure_file_exists(showname+'.ident.'+gmm+'.seg')


def manage_ident(showname, gmm, clusters):
	f = open("%s.ident.%s.seg" % (showname,gmm ) ,"r")
	for l in f:
		 if l.startswith(";;"):
			cluster, speaker = l.split()[ 1 ].split(':')[ 1 ].split('_')
			i = l.index('score:'+speaker) + len('score:'+speaker+" = ")
			ii = l.index(']',i) -1
			value = l[i:ii]
			if clusters[ cluster ].has_key( speaker ) == False:
				clusters[ cluster ][ speaker ] = float(value)
			else:
				if clusters[ cluster ][ speaker ] < float(value):
					clusters[ cluster ][ speaker ] = float(value)
	f.close()
	if not keep_intermediate_files:
		os.remove("%s.ident.%s.seg" % (showname,gmm ) )

def wave_duration(wavfile):
	import wave
	w = wave.open(wavfile)
	par = w.getparams()
	w.close()
	return par[3]/par[2]

def merge_waves(input_waves,wavename):
	""" Takes a list of waves and append them all to a brend new destination wave """
	if os.path.exists(wavename):
		raise Exception("File gmm %s already exist!" % wavename)
	waves = [w.replace(" ","\ ") for w in input_waves]
	w=" ".join(waves)
	commandline = "sox "+str(w)+" "+ str(wavename)
	start_subprocess(commandline)
	
def build_gmm(show,name):
	""" Build a gmm (Gaussian Mixture Model) file from a given wave """
	
	diarization(show)

	ident_seg(show,name)

	extract_mfcc(show)

	train_init(show)

	train_map(show)
	



def extract_speakers(file_input):
	cpus = cpu_count()
	clusters = {}
	start_time = time.time()
	video2trim( file_input )
	basename, extension = os.path.splitext( file_input )
	seg2srt(basename+'.seg')
	extract_mfcc( basename )
	
	print "*** voice matching ***"
	extract_clusters( "%s.seg" %  basename, clusters )
	p = {}
	files_in_db = [ f for f in os.listdir(db_dir) if f.endswith('.gmm') ]
	for f in files_in_db:
		if  len(active_children()) < (cpus-1) :
			p[f] = Process(target=mfcc_vs_gmm, args=( basename, f ) )
			p[f].start()
		else:
			while len(active_children()) >= cpus:
				time.sleep(1)	
			p[f] = Process(target=mfcc_vs_gmm, args=( basename, f ) )
			p[f].start()
	for proc in p:
		if p[proc].is_alive():
			p[proc].join()	
	
	for f in files_in_db:
		manage_ident( basename, f , clusters)
	print ""
	speakers = {}
	for c in clusters:
	    print c
	    value = -33.0
	    best = 'unknown'
            speakers[c] = 'unknown'
	    for cc in clusters[c]:
		if clusters[c][cc] > value:
			value = clusters[c][cc]
			best = cc
			speakers[c] = cc
		print "\t %s %s" % (cc , clusters[c][cc])
	    print '\t ------------------------'
	    array = clusters[c].values()
	    array.sort()
	    array.reverse()
	    distance = abs(array[1]) - abs(array[0])
	    mean = sum(array) / len(array)
	    m_distance = abs(mean) - abs(array[0])
            if distance < .1 :
		    best = 'unknown'
		    speakers[c] = best
	    print '\t best speaker: %s (distance from 2nd %f - mean %f - distance from mean %f ) ' % (best , distance, mean, m_distance)
        srt2subnames(basename, speakers)
	sec = wave_duration(basename+'.wav')
	total_time = time.time() - start_time
	print "\nwav duration: %s\nall done in %dsec (%s) with %s cpus" % ( humanize_time(sec), total_time, humanize_time(total_time), cpus )


def remove_blanks_callback(option, opt_str, value, parser):
	"""Remove all white spaces in filename and substitute with underscores"""
	if len(parser.rargs) == 0:
		parser.error("incorrect number of arguments")
	file_input=str(parser.rargs[0])
	new_file_input = file_input
	new_file_input=new_file_input.replace("'",'_').replace('-','_').replace(' ','_')
	os.rename(file_input,new_file_input)
	ensure_file_exists(new_file_input)
	file_input=new_file_input
	if getattr(parser.values, option.dest):
                args.extend(getattr(parser.values, option.dest))
	setattr(parser.values, option.dest, file_input)           

def multiargs_callback(option, opt_str, value, parser):
	"""Create an array from multiple args"""
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

if __name__ == '__main__':
	usage = "usage: %prog [options] arg"
	parser = OptionParser(usage)
	#parser.add_option("-v", "--verbose", dest="verbose", default=False)
	parser.add_option("-i", "--input", action="callback",callback=remove_blanks_callback, metavar="FILE", help="read input video or audio file", dest="file_input")
	parser.add_option("-g", "--gmm", action="callback", callback=multiargs_callback, dest="waves_for_gmm")
	parser.add_option("-s", "--speaker", dest="speaker_for_gmm")
	parser.add_option("-d","--db",type="string", dest="dir_gmm", metavar="PATH",default=os.path.expanduser("~/.gmm_db"),help="Change the path of the gmm db.")
	parser.add_option("-j","--jar",type="string", dest="dir_jar", metavar="PATH",help="Change the path of the jar LIUM.")
	(options, args) = parser.parse_args()
	print len(args)
	#if len(args) == 0:
	#	parser.error("incorrect number of arguments")
	#check_deps()
	if options.file_input:
		if options.dir_gmm:
			db_dir = options.dir_gmm
		if options.dir_jar:
			lium_jar = options.dir_jar	
		check_deps()
		extract_speakers(options.file_input)
		exit(0)
	if options.waves_for_gmm and options.speaker_for_gmm:
		if options.dir_gmm:
			db_dir = options.dir_gmm
		check_deps()
		show = None
		waves = options.waves_for_gmm
		speaker = options.speaker_for_gmm
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
	
	
	
	
	
