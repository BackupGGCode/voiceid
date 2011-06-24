#!/bin/bash

#input wave file, %s will be substituted with $show
show=$1

/usr/bin/java -Xmx2024m -jar ./LIUM_SpkDiarization.jar  --help --fInputMask=%s.wav --sOutputMask=%s.seg --doCEClustering $show

./feat_sphinx.sh $show.wav $show.mfcc $show.uem.seg $show

java -Xmx2024m -cp LIUM_SpkDiarization.jar fr.lium.spkDiarization.programs.MTrainInit --help --sInputMask=%s.seg --fInputMask=%s.wav --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --emInitMethod=copy --tInputMask=./ubm.gmm --tOutputMask=%s.init.gmm $show

java -Xmx2024m -cp LIUM_SpkDiarization.jar fr.lium.spkDiarization.programs.MTrainMAP --help --sInputMask=%s.seg --fInputMask=%s.mfcc --fInputDesc="audio16kHz2sphinx,1:3:2:0:0:0,13,1:1:300:4"  --tInputMask=%s.init.gmm --emCtrl=1,5,0.01 --varCtrl=0.01,10.0 --tOutputMask=%s.gmm $show




