#!/usr/bin/env python 
import fileinput


def humanize_time(secs):
	mins, secs = divmod(secs, 60)
	hours, mins = divmod(mins, 60)
	return '%02d:%02d:%02d,%s' % (hours, mins, int(secs), str(("%0.3f" % secs))[-3:])

fileoutput = "output.srt"
FILE = open(fileoutput, "w")
row = 0
word = "SPEAKER"
for line in fileinput.input():
	row = row + 1
	FILE.write(str(row) + "\n")

	FILE.write(humanize_time(float(line.split()[0])) + " --> " + humanize_time(float(line.split()[1])) + "\n")
	FILE.write(line.split()[2].split('-')[-1] + "\n")
	FILE.write("" + "\n")
		
FILE.close()	
	#print line
FILE = open(fileoutput, "r")
#for l in FILE:
#	print l

FILE.close()
