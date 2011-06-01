#!/bin/bash


videofile=$1


./video2trim.sh "$videofile"


directory=$(dirname "$1")
show=`basename "$1"`
_show=$( echo "$show" | sed -e 's/ /_/g' | sed -e 's/\\//g' ) 
#mv -n "$directory"/"$show" "$directory"/"$_show"
show="$directory"/$_show
#echo $show
#exit 1

if [ -f "$show" ] ; then
    # name without extension
    name=${show%\.*}
 #   echo ${name} 
fi ;

speakers_in_video=$(ls $name)
echo "speakers in video = " $speakers_in_video


speakers_in_db=$(ls db)
echo "speakers in db = " $speakers_in_db



for speaker_v in $speakers_in_video
do
	speaker_samples=$( ls $name/$speaker_v )


	for speaker_db in $speakers_in_db
	do

		original_speak=$(cat db/$speaker_db/speakers.txt)
		similar=0
		different=0

		for sample in $speaker_samples
		do 
			printf "speaker_v %s | sample %s | speaker_db %s\n"  "$speaker_v"  $sample $speaker_db
			num_speak=$(  ./test_2_speakers.sh db/$speaker_db/*wav $name/$speaker_v/$sample 2>&1 |grep ";;" | wc -l  )
			seconds=$( soxi -s $name/$speaker_v/$sample )
			if (( $num_speak <= $original_speak  ))
			then 
				similar=$(( $similar + $seconds   ))	
			else
				different=$(( $different + $seconds ))	
			fi

		done
		total=$(( $similar + $different ))
		echo statistics for speaker $speaker_v
		echo similarity = $((  (100 *  $similar  ) / $total  )) % 

	done
	printf "*********\n"
done
