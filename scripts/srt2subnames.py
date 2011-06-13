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
        return word_dic[match.group(0)]+'\n'
    
    return rc.sub(translate, text)




# argv is your commandline arguments, argv[0] is your program name, so skip it
original_subtitle = open(sys.argv[1], "r")
result_extract_video = open(sys.argv[2], "r")

key_value = {}
file_result_extract_video = result_extract_video.readlines()
file_original_subtitle = original_subtitle.read()

key_value = eval(file_result_extract_video[0])
key_value=dict(map(lambda (key, value): (str(key)+"\n", value), key_value.items()))
str3 = replace_words(file_original_subtitle, key_value)
out_file = sys.argv[1]+"_new.srt"
# create a output file
fout = open(out_file, "w")
fout.write(str3)

fout.close()
result_extract_video.close()
original_subtitle.close()
