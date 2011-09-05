#!/usr/bin/env python 
from optparse import OptionParser
from multiprocessing import Process, cpu_count, active_children
import os
import shlex, subprocess
import sys, signal
import time
import re
import string
import shutil, struct

def get_gender(input_file):
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


    gender = gmm.read(1)
    #print gender
    return gender
    #all_other = gmm.read()


if __name__ == '__main__':
    
    if not os.path.exists("M"):
        os.makedirs("M")
    if not os.path.exists("F"):
        os.makedirs("F")
    if not os.path.exists("U"):
        os.makedirs("U")
        
    for f in os.listdir(os.getcwd()):
        if f.endswith('.gmm'):
            g = get_gender(f)
            shutil.move(f,g)
    """
    files_in_db = {}
	files_in_db["M"] = [ f for f in os.listdir("M")) if f.endswith('.gmm') ]
	files_in_db["F"] = [ f for f in os.listdir(os.path.join(db_dir,"F")) if f.endswith('.gmm') ]
	files_in_db["U"] = [ f for f in os.listdir(os.path.join(db_dir,"U")) if f.endswith('.gmm') ]
    """
