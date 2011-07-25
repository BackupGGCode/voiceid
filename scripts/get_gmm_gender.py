#!/usr/bin/env python 


import struct
import sys

if __name__ == '__main__':

	input_file = sys.argv[1]

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
	print gender 

	all_other = gmm.read()

	"""
	gaussian_kind = struct.unpack('>i', gmm.read(4) )

	dim = struct.unpack('>i', gmm.read(4) )

	nb_comp = struct.unpack('>i', gmm.read(4) )

	"""

	gmm.close()
