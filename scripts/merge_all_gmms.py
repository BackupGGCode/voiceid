#!/usr/bin/env python 
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
from voiceid import merge_gmms

def get_speaker(input_file):
    #input_file = sys.argv[1]

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

  
    print name
    return name
    #all_other = gmm.read()

if __name__ == '__main__':

    speakers = {}
    
    for f in os.listdir(os.getcwd()):
        if f.endswith('.gmm'):
            s = get_speaker(f)
	    if not speakers.has_key(s):
		speakers[s] = []
	    speakers[s].append(f)
    	
    print speakers

	
    for sp in speakers:  
	out = sp+"__t.gmm"
        merge_gmms(speakers[sp],out)    

