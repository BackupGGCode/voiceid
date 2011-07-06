#!/bin/bash 

#input wave file, %s will be substituted with $show
LIUM=./LIUM_SpkDiarization.jar
show="$1"
speaker="$2"

/usr/bin/java -Xmx2024m -jar $LIUM  --help --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering $show

./feat_sphinx.sh $show.wav $show.mfcc $show.uem.seg $show

if [ -n "$2" ]
then 
	speakers=( $(awk '/cluster:S[0-9]/ {p=substr($2,9); print p} '  $show.seg | uniq ) )
	echo -n "" > ${show}.ident.seg
	while read line
	do 
		currentline=$line
		for s in  ${speakers[@]}
		do 	
			currentline=$(echo $currentline | sed -e "s/$s/$speaker/g" )
		done
		echo $currentline >> ${show}.ident.seg
	done < "${show}.seg"
fi

java -Xmx2024m -cp $LIUM fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=%s.ident.seg --fInputMask=%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=./ubm.gmm --tOutputMask=%s.init.gmm $show

java -Xmx2024m -cp $LIUM fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=%s.ident.seg --fInputMask=%s.mfcc --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm $show




