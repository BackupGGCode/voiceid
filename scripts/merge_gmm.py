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

from voiceid.fm import merge_gmms
import shutil
import sys


if __name__ == '__main__':

	input_files = sys.argv[1:-1]
	output_file = sys.argv[-1:]
	if len(input_files) + len(output_file) < 2:
		print 'not enough arguments'
		exit(0)
	if len(input_files) == 1 and len(output_file) == 1:
		shutil.copy(input_files[0], output_file[0])
		exit(0)

	output_file = output_file[0]
	merge_gmms(input_files, output_file)

