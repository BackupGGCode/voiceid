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


import struct
import sys

if __name__ == '__main__':

	input_file = sys.argv[1]

	gmm = open(input_file, 'r')

	kind = gmm.read(8)

	num_gmm_string = gmm.read(4) 
	num_gmm = struct.unpack('>i', num_gmm_string)

	if num_gmm != (1,):
		print str(num_gmm) + " gmms"
		raise Exception('Loop needed for gmms')


	gmm_1 = gmm.read(8)

	nothing = gmm.read(4) 

	str_len = struct.unpack('>i', gmm.read(4))
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
