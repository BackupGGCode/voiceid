#!/usr/bin/env python 

import shutil
import struct
import sys
from voiceid import merge_gmms


if __name__ == '__main__':

	input_files = sys.argv[1:-1]
	output_file = sys.argv[-1:]
	if len(input_files) + len(output_file) < 2:
		print 'not enough arguments'
		exit(0)
	if len(input_files) == 1 and len(output_file) == 1:
		shutil.copy(input_files[0],output_file[0])
		exit(0)

	output_file = output_file[0]
	merge_gmms(input_files,output_file)

