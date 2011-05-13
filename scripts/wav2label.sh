#!/bin/bash

show=`basename $1 .wav`

myjava=java
LIUM=LIUM_SpkDiarization-4.7.jar

$myjava -Xmx2024m  -jar $LIUM  --fInputMask=./$1  --sOutputMask=./$show.seg --doCEClustering  $show

$myjava -cp $LIUM fr.lium.spkDiarization.tools.SPrintSeg  --help --sInputMask=$show.seg --sOutputMask=$show.ctl --sOutputFormat=ctl $show


echo '#!/usr/bin/perl -w
use strict;

while (<>) {
    chomp;
    my ($show, $sf, $ef, $uttid) = split;
    $sf /= 100;
    $ef /= 100;
    print "$sf\t$ef\t$uttid\n";
} ' >convert.pl

perl convert.pl  $show.ctl > $show.txt

sort -g $show.txt >.tmp.txt
mv .tmp.txt $show.txt

