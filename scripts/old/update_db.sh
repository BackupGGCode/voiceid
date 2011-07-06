#!/bin/bash




function build_speaker(){
speaker=$1


sox db/$speaker/*wav ${speaker}_train.wav

./wav2label.sh ${speaker}_train.wav   2>&1 > /dev/null
echo  $(cat ${speaker}_train.seg |grep -c ";;") > db/$speaker/speakers.txt
rm db/$speaker/*wav
mv ${speaker}_train.wav db/$speaker/
rm ${speaker}_train.*
}

if [ -z "$1" ]
then 

	speakers_in_db=$(ls db)

	for speaker_db in $speakers_in_db  
	do
		build_speaker $speaker_db

	done
else

	build_speaker "$1"
fi

