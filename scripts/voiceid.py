#!/usr/bin/env python 

from multiprocessing import Process, cpu_count, active_children
import os
import shlex, subprocess
import sys, signal
import time
import re
p = None
verbose = False

lium_jar='./LIUM_SpkDiarization.jar'
db_dir = './gmm_db'

dev_null = open('/dev/null','w')
if verbose:
	dev_null = None

def start_subprocess(commandline):
	args = shlex.split(commandline)
	p = subprocess.Popen(args, stdout=dev_null, stderr=dev_null)
	retval = p.wait()
	if retval != 0: 
		raise Exception("Subprocess closed unexpectedly "+str(p) )
def ensure_file_exists(filename):
	if not os.path.exists(filename):
		raise Exception("File %s not correctly created"  % filename)
	if not (os.path.getsize(filename) > 0):
		raise Exception("File %s empty"  % filename)

def humanize_time(secs):
	mins, secs = divmod(secs, 60)
	hours, mins = divmod(mins, 60)
	return '%02d:%02d:%02d,%s' % (hours, mins, int(secs), str(("%0.3f" % secs ))[-3:] )

def video2wav(show):
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


def diarization(showname):
	start_subprocess( 'java -Xmx2024m -jar '+lium_jar+'   --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering '+  showname )

def seg2trim(segfile):
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
	s.close()

def seg2srt(segfile):
	def readl(s):
		total = []
		for line in s.readlines():
			if not line.startswith(";;"):
				arr=line.split()
				total.append(arr)
		s.close()
		return total

	def readtime(aline):
		return int(aline[2])

	basename, extension = os.path.splitext(segfile)	
	s = open(segfile,'r')
	lines=readl(s)
	lines.sort(key=readtime, reverse=False)
	fileoutput = basename+".srt"
	FILE = open(fileoutput,"w")
	row = 0
	for line in lines:
		row = row +1
		FILE.write(str(row)+"\n")
		FILE.write(humanize_time(float(line[2])) + " --> " + humanize_time(float(line[2])+float(line[3]))+"\n")
		FILE.write(line[7]+"\n")
		FILE.write(""+"\n")
			
	FILE.close()

def video2trim(videofile):
	print "*** converting video to wav ***"
	video2wav(videofile)
	show, ext = os.path.splitext(videofile)
	print "*** diarization ***"
	diarization(show)
	print "*** trim ***"
	seg2trim(show+'.seg')

def extract_mfcc(show):
	commandline = "sphinx_fe -verbose no -mswav yes -i %s.wav -o %s.mfcc" %  ( show, show )
	start_subprocess(commandline)

def ident_seg(showname,name):
	f = open(showname+'.seg','r')
	clusters=[]
	lines = f.readlines()
	for line in lines:
		for k in line.split():
			if k.startswith('cluster:'):
				prefix,c = k.split(':')
				clusters.append(c)
	f.close()
	output = open(showname+'ident.seg', 'w')
	clusters.reverse()
	for line in lines:
		for c in clusters:
			line.replace(c,name)
		output.write(line+'\n')
	output.close()

def train_init(show):
	commandline = 'java -Xmx2024m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=%s.ident.seg --fInputMask=%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=./ubm.gmm --tOutputMask=%s.init.gmm '+show
	start_subprocess(commandline)

def train_map(show):
	commandline = 'java -Xmx2024m -cp '+lium_jar+' fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=%s.ident.seg --fInputMask=%s.mfcc --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm ' + show 
	start_subprocess(commandline)

def srt2subnames(showname, key_value):
	def replace_words(text, word_dic):
	    """
	    take a text and replace words that match a key in a dictionary with
	    the associated value, return the changed text
	    """
	    rc = re.compile('|'.join(map(re.escape, word_dic)))
		
	    def translate(match):
		return word_dic[match.group(0)]+'\n'
	    
	    return rc.sub(translate, text)

	file_original_subtitle = open(showname+".srt") #FIXME: open file in function
	original_subtitle = file_original_subtitle.read()
	file_original_subtitle.close()
	key_value=dict(map(lambda (key, value): (str(key)+"\n", value), key_value.items()))
	str3 = replace_words(original_subtitle, key_value)
	out_file = showname+"_new.srt"
	# create a output file
	fout = open(out_file, "w")
	fout.write(str3)
	fout.close()	

def extract_clusters(filename, clusters):
	f = open(filename,"r")
	for l in f:
		 if l.startswith(";;") :
			ll = l.split()[1].split(':')[1]	
			clusters[ll] = {}
	f.close()

def mfcc_vs_gmm(showname, gmm):
	commandline = 'java -Xmx2G -Xms2G -cp '+lium_jar+'  fr.lium.spkDiarization.programs.MScore --sInputMask=%s.seg   --fInputMask=%s.mfcc  --sOutputMask=%s.ident.'+gmm+'.seg --sOutputFormat=seg,UTF8  --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:0:300:4" --tInputMask='+db_dir+'/'+gmm+' --sTop=8,ubm.gmm  --sSetLabel=add --sByCluster '+  showname 
	start_subprocess(commandline)


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

def wave_duration(wavfile):
	import wave
	w = wave.open(wavfile)
	par = w.getparams()
	w.close()
	return par[3]/par[2]

def build_gmm(show,name):
	
	diarization(show)

	ident_seg(show,name)

	extract_mfcc(show)

	train_init(show)

	train_map(show)



if __name__ == '__main__':
	cpus = cpu_count()
	clusters = {}
	#print '%s processors' % cpus
	start_time = time.time()
	file_input = sys.argv[ 1: ] 
	if len( file_input ) > 1: #blanks in file name
		print file_input
		new_file_input = '_'.join(file_input).replace("'",'_').replace('-','_')
		os.rename(' '.join(file_input),new_file_input)
		file_input = new_file_input
	else:
		new_file_input = file_input[0].replace("'",'_').replace('-','_').replace(' ','_')
		os.rename( file_input[0], new_file_input )
	file_input = new_file_input

	video2trim( file_input )
	basename, extension = os.path.splitext( file_input )
	seg2srt(basename+'.seg')
	extract_mfcc( basename )
	
	print "*** voice matching ***"
	extract_clusters( "%s.seg" %  basename, clusters )
	p = {}
	files_in_db = [ f for f in os.listdir(db_dir) if f.endswith('.gmm') ]
	for f in files_in_db:
		#print "len(active_children()) %d" % len(active_children() )
		if  len(active_children()) < (cpus-1) :
			p[f] = Process(target=mfcc_vs_gmm, args=( basename, f ) )
			p[f].start()
		else:
			while len(active_children()) >= cpus:
				#print "len(active_children()) %d" % len(active_children() )
				time.sleep(1)	
			p[f] = Process(target=mfcc_vs_gmm, args=( basename, f ) )
			p[f].start()
	for proc in p:
		if p[proc].is_alive():
			print 'joining proc %s' % str(proc)
			p[proc].join()	
	
	#print "Processes %s" % active_children()
	for f in files_in_db:
		manage_ident( basename, f , clusters)
	print ""
	speakers = {}
	#print clusters
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

