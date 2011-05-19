#!/bin/bash

show=`basename "$1"`
_show=$( echo "$show" | sed -e 's/ /_/g' | sed -e 's/\\//g' ) 
mv "$show" "$_show"
show=$_show
#echo $show
#exit 1

if [ -f "$show" ] ; then
    # name without extension
    name=${show%\.*}
    echo ${name} 
fi ;

gst-launch-0.10 filesrc location="$show" ! decodebin  ! audioresample ! 'audio/x-raw-int,rate=16000' !  audioconvert ! 'audio/x-raw-int,rate=16000,depth=16,signed=true,channels=1'    ! wavenc !   filesink location=${name}.wav

./wav2label.sh ${name}.wav 
./seg2trim.sh ${name}.seg


