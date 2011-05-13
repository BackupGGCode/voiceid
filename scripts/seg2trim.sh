#!/bin/bash 


input_file=$1
filename=$( basename $1 .seg )
declare  -a a
a=( $(cat $1 | grep -v ";;" ) )

lines=$(cat $1 | grep -v ";;" | wc -l )
#echo $lines
#echo ${a[@]}

mkdir -p  $filename

for((i=0;i<$[ $lines * 7 ];i+=8)){

A0=${a[$i]} 
A1=$( echo "scale=2; ${a[ $(( $i+2 )) ]} /100 " | bc )
A2=$( echo "scale=2; ${a[ $(( $i+3 )) ]} /100 " | bc )
A3=${a[ $(( $i+7 ))  ]} 
#set -- "${a[$i]}"

COMMAND=$(printf "sox %s.wav $filename/%s_%s.wav  trim %s %s\n" "$filename" "$A3" "$A1" "$A1" "$A2" )
echo $COMMAND
$COMMAND
#echo  " sox  ${filename}.wav  $A3_   $A0 $A1 $A2 $A3" 
 
}

