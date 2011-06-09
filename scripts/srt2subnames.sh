#!/usr/bin/env python 
import fileinput
import sys
import re
word = "best"

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
for n in sys.argv[1:]:
    print(n) #print out the filename we are currently processing
    original_subtitle = open(sys.argv[1], "r")
    result_extract_video = open(sys.argv[2], "r")

    key_value = {}
    for line2 in result_extract_video:
	key_value.append(str(line2.split()[0]) + ':' + str(line2.split()[1]))
		
    replace_words(original_subtitle, word_dic)
    # do some processing
    input.close()
