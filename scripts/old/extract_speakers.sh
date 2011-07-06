#!/bin/bash


start_time=$(date +%s)

processors=$(( $(grep -c ^processor /proc/cpuinfo  || sysctl  hw.ncpu | awk '{print $2}'  )  -1 ))
#processors=15
videofile=$1

if [ -z "$videofile" ]
then
	echo "Error: parameter missing, file name required"
	echo " example:"
	echo "          ./extract_speakers.sh  myfilename.mp4"

	exit 0
fi 

video_duration="Video $(ffprobe "$videofile" 2>&1 |grep Duration)"


function kill_child(){
#	echo *********** kill_child
	all_jobs=$(jobs -p)

	for j in $all_jobs
	do 
		kill -9 $j 2>&1 > /dev/null
	done
	exit 0
}

#trap "kill_child" SIGABRT
#trap "kill_child" SIGKILL
#trap "kill_child" SIGTERM
trap "kill_child" SIGINT
#trap -p




max_score=0
best_speaker_name="unknown"

lockfile .extract_speakers.lock
echo 0 > .max_score
echo unknown > .best_speaker_name
rm -f .extract_speakers.lock

./video2trim.sh "$videofile"

function speakerdb_vs_samples (){

		speaker_db=$1
		speaker_samples=$2		

		original_speak=$(cat db/$speaker_db/speakers.txt)
		similar=0
		different=0
		reportname=${speaker_v}_vs_${speaker_db}.txt	
		echo "${speaker_v}_vs_${speaker_db}" > $reportname
		for sample in $speaker_samples
		do 
			seconds=$( soxi -s $name/$speaker_v/$sample )
			sec=$( soxi -D $name/$speaker_v/$sample )
			if [ $seconds -gt 48000 ]
			then
				printf "speaker_v %s | sample %13s | speaker_db %10s %s "  "$speaker_v"  $sample $speaker_db $sec   >> $reportname
				num_speak=$(  ./test_2_speakers.sh db/$speaker_db/*wav $name/$speaker_v/$sample 2>&1 |grep -c ";;" )
				if (( $num_speak <= $original_speak  ))
				then 
					similar=$(( $similar + $seconds   ))	
					printf "*\n" >> $reportname
				else
					different=$(( $different + $seconds ))	
					printf "\n" >> $reportname
				fi
			fi

		done
		
		total=$(( $similar + $different ))
		lockfile .extract_speakers.lock
		if (( $total != 0 ))
		then
			echo "statistics for speaker $speaker_v" >> $reportname
			sim=$((  (100 *  $similar  ) / $total  ))
			echo similarity = $sim %  >> $reportname
			
			cat $reportname
	
			current_score=$((  (100 *  $similar  ) / $total  ))
			
			max_score=$( cat .max_score )
			if (( $max_score < $current_score )) 	
			then
				echo $current_score > .max_score
				echo ${speaker_db} > .best_speaker_name
			fi	
			echo -e "\t${speaker_db} \t $current_score%" >>$totalreport
		fi
		rm -f .extract_speakers.lock

}

directory=$(dirname "$1")
show=`basename "$1"`
_show=$( echo "$show" | sed -e 's/ /_/g' | sed -e 's/\\//g' ) 
#mv -n "$directory"/"$show" "$directory"/"$_show"
totalreport=${_show}_SPEAKERS.txt
reportcodename=${_show}_small_report.txt
echo -n "{" > $reportcodename
show="$directory"/$_show
#echo $show
#exit 1

if [ -f "$show" ] ; then
    # name without extension
    name=${show%\.*}
 #   echo ${name} 
fi ;
echo "$name" >$totalreport

speakers_in_video=$(ls $name)
echo "speakers in video = " $speakers_in_video

speakers_in_db=""

a_speakers_in_db=$(ls db)
for s in $a_speakers_in_db
do 
	echo Checking db for speaker $s
	if [ -f db/$s/*.wav ] && [ -f db/$s/speakers.txt ] && [ "$(cat db/$s/speakers.txt | grep "[^0-9]" > /dev/null;echo $? )" -eq 1 ]
	then
		speakers_in_db="$speakers_in_db $s"
	fi
done

echo "speakers in db = " $speakers_in_db

declare -a bg_process
total_samples=0
echo "*** Starting Speaker Recognition ***"
for speaker_v in $speakers_in_video
do
	best_speaker_name="unknown"
	max_score=0
	
	lockfile .extract_speakers.lock
	echo 0 > .max_score
	echo unknown > .best_speaker_name
	rm -f .extract_speakers.lock

	speaker_samples=$( ls $name/$speaker_v )
	n_s=( $speaker_samples )
	total_samples=$(( $total_samples + ${#n_s[@]} ))

	echo "$speaker_v:" >> $totalreport

	for speaker_db in $speakers_in_db  
	do
		if ((  ${#bg_process[@]}  < $processors ))
		then
			echo " $processors processors"
			echo " ${#bg_process[@]} processes"
			speakerdb_vs_samples "$speaker_db"  "$speaker_samples" &
			pid=$!
			index=${#bg_process[@]}
			bg_process[ $index  ]=$pid
			echo starting process num $index with pid $pid
                else
			while (( ${#bg_process[@]}     >=   $processors   ))
			do 
#				echo " $processors processors"
#				echo " ${#bg_process[@]} processes"
				for proc in seq 0 $(( ${#bg_process[@]} -1 ))
				do
					if  [  -n "${bg_process[$proc]}" ]  &&  [ -z "$( ps hp ${bg_process[$proc]} | grep -v PID  )" ]
					then
						unset bg_process[$proc]
#						echo unset proc $proc
					fi
				done
				sleep 2
			done
 			speakerdb_vs_samples "$speaker_db"  "$speaker_samples" &
			pid=$!
			index=${#bg_process[@]}
			bg_process[ $index  ]=$pid
			echo starting process num $index with pid $pid
		fi
	done
	while (( ${#bg_process[@]}  > 0     ))
	do 
#		echo " $processors processors"
#		echo " ${#bg_process[@]} processes"
		for proc in ${!bg_process[@]} 
		do
#			echo "bg_process[$proc]= ${bg_process[$proc]}"
			if [  -n "${bg_process[$proc]}" ]  && [ -z "$( ps hp ${bg_process[$proc]} | grep -v PID )" ]
			then
				unset bg_process[$proc]
			fi
		done
		sleep 3
	done
	best_speaker_name=$( cat .best_speaker_name )
	echo -e "\tbest speaker: \t$best_speaker_name" >> $totalreport
	#echo -e "$speaker_v $best_speaker_name" >> $reportcodename
	echo -n "'$speaker_v':'$best_speaker_name'," >> $reportcodename
	

	printf "*********\n"
	
done
echo -e "}" >> $reportcodename
python srt2subnames.py ${name}.srt ${_show}_small_report.txt
#vlc --play-and-stop $videofile --sub-file ${name}.srt_new.srt
cat $totalreport
#cat $reportcodename
end_time=$(date +%s)
total_seconds=$((end_time - $start_time ))
h=$(( $total_seconds/3600 ))
m=$(( $total_seconds/60 ))
s=$(( $total_seconds%60 ))
number_of_clusters=( $speakers_in_video )

total_speakers=( $(echo $speakers_in_db) )
echo
echo "Performance Report:"
echo  "  $video_duration"
echo  "  $processors processors "
echo  "  ${#total_speakers[@]} speakers in db "
echo  "  ${#number_of_clusters[@]} clusters "
echo  "  $total_samples total samples "

printf "  time spent: %2d:%2d:%2d (%ds)  \n" $h $m $s ${total_seconds}
