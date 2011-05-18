#!/bin/bash 


wave_1=$1
wave_2=$2

temp_wav_basename=$(mktemp --tmpdir=./ )
temp_wav=${temp_wav_basename}.wav

sox $wave_1 $wave_2 $temp_wav

./wav2label.sh ${temp_wav}

echo  $(grep ";;" ${temp_wav_basename}.seg |wc -l ) different speakers

rm ${temp_wav_basename}*
