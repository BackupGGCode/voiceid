#!/bin/bash

directory=$(dirname "$1")
show=`basename "$1"`
_show=$( echo "$show" | sed -e 's/ /_/g' | sed -e "s/'/_/g" | sed -e 's/\\//g' ) 

if [ "$show" != "$_show" ]
then 
	mv -f "$directory"/"$show" "$directory"/"$_show"
fi
show="$directory"/$_show
#echo $show
#exit 1

if [ -f "$show" ] ; then
    # name without extension
    name=${show%\.*}
    echo ${name} 
fi ;
echo "*** Extracting Wav ***"

if [ "$show" == "${name}.wav" -a -f "${name}.wav"  -a  -n "$(file  $show |grep  "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz" )" ]
then
	echo "Already in Wave format"	
else
	gst-launch-0.10 filesrc location="$show" ! decodebin  ! audioresample ! 'audio/x-raw-int,rate=16000' !  audioconvert ! 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1'    ! wavenc !   filesink location=${name}.wav
fi
echo "*** Wav done ***"

echo "*** Extracting features ***"
./feat_sphinx.sh ${name}.wav ${name}.mfcc ${name}.uem.seg
echo "*** Features done ***"

echo "*** Starting Diarization ***"
./wav2label.sh ${name}.wav 
./label2srt.py ${name}.txt
mv output.srt ${name}.srt 
echo "*** Diarization done***"
echo "*** Splitting audio file***"
./seg2trim.sh ${name}.seg
echo "*** Split done***"

