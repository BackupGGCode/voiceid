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


from voiceid.fm import split_gmm, rename_gmm, merge_gmms
import os
import shutil
import struct
import sys



if __name__ == '__main__':
    
    input_file = sys.argv[1]
    input_name = sys.argv[2]
    
    if len(input_file) + len(input_name) < 2:
        print 'not enough arguments'
        exit(0)

    output_dir = input_file + "gmms_temp"
    os.makedirs(output_dir)
    split_gmm(input_file, output_dir)
    files = os.listdir(output_dir)
    files_path = [os.path.join(output_dir, f) for f in files]
    for f in files_path:
        rename_gmm(f, input_name)
    
    files_path = [os.path.join(output_dir, f) for f in files]
    
    merge_gmms(files_path, input_name + ".gmm")
    
    os.remove(input_file) 
        
    shutil.rmtree(output_dir)
    
        
