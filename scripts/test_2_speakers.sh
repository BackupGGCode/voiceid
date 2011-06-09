#!/bin/bash


wave_1="$1"
wave_2="$2"

macosx=$(uname -a |grep "Darwin Kernel Version" )
if [ -n "$macosx" ]
then
temp_wav_basename=$(basename $(mktemp -t t2s) )
else
temp_wav_basename=$(mktemp --tmpdir=./ )
fi


temp_wav=${temp_wav_basename}.wav

sox $wave_1 $wave_2 $temp_wav

./wav2label.sh ${temp_wav}

echo  $(grep ";;" ${temp_wav_basename}.seg |wc -l ) different speakers
echo -------------- seg file ----------------
cat ${temp_wav_basename}.seg
echo ---------- end seg file ----------------
rm ${temp_wav_basename}*
