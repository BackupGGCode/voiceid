#!/usr/bin/env python 

from multiprocessing import Process
import os
import shlex, subprocess
import sys, signal

p = None
clusters = {}
def termHandler(a,b):
	print "termHandler"
	p.kill()

signal.signal(signal.SIGINT, termHandler )

def video2trim(videofile):
	commandline = './video2trim.sh %s' %  videofile
	args = shlex.split(commandline)
	p = subprocess.call(args)

	

def extract_clusters(filename):
	f = open(filename,"r")
	for l in f:
		 if l.startswith(";;") :
			ll = l.split()[1].split(':')[1]	
			clusters[ll] = {}
	f.close()

def mfcc_vs_gmm(showname, gmm):
	commandline =' java -Xmx2G -Xms2G -cp ./LIUM_SpkDiarization.jar  fr.lium.spkDiarization.programs.MScore --help   --sInputMask=%s.seg   --fInputMask=%s.mfcc  --sOutputMask=%s.ident.'+gmm+'.seg --sOutputFormat=seg,UTF8  --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:0:300:4" --tInputMask='+gmm+' --sTop=5,ubm.gmm  --sSetLabel=add --sByCluster '+  showname
	args = shlex.split(commandline)
	p = subprocess.call(args)
	f = open("%s.ident.%s.seg" % (showname,gmm ) ,"r")
	for l in f:
		 if l.startswith(";;"):
			cluster, speaker = l.split()[ 1 ].split(':')[ 1 ].split('_')
			i = l.index('score:'+speaker) + len('score:'+speaker+" = ")
			ii = l.index(']',i) -1
			value = l[i:ii]
			clusters[ cluster ][ speaker ] = float(value)
	f.close()

if __name__ == '__main__':
	file_input = sys.argv[ 1 ] 
	video2trim( file_input )
	basename, extension = os.path.splitext( file_input )
	
	extract_clusters( "%s.seg" %  basename )

	for f in os.listdir('./gmm_db'):
		if f.endswith('.gmm'):
			mfcc_vs_gmm( basename, f )
	for c in clusters:
	    print c
	    for cc in clusters[c]:
		print "\t %s %s" % (cc , clusters[c][cc])


