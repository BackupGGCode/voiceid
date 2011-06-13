#!/usr/bin/env python 
import fileinput
import sys
import re

def replace_words(text, word_dic):
    """
    take a text and replace words that match a key in a dictionary with
    the associated value, return the changed text
    """
    rc = re.compile('|'.join(map(re.escape, word_dic)))
	
    def translate(match):
        return word_dic[match.group(0)]
    
    return rc.sub(translate, text)




# argv is your commandline arguments, argv[0] is your program name, so skip it
original_subtitle = open(sys.argv[1], "r")
result_extract_video = open(sys.argv[2], "r")

key_value = {}
file_result_extract_video = result_extract_video.readlines()
file_original_subtitle = original_subtitle.read()

#first_line = file_result_extract_video[0]
#file_result_extract_video[0]=first_line[:-1]

key_value = eval(file_result_extract_video[0])
#for line2 in file_result_extract_video:
#	if len(line2) != 0:
#		key_value[str(line2.split()[0])+'\n'] = str(line2.split()[1])

str3 = replace_words(file_original_subtitle, key_value)

out_file = sys.argv[1]+"_new.srt"
# create a output file
fout = open(out_file, "w")
fout.write(str3)

fout.close()
result_extract_video.close()
original_subtitle.close()
