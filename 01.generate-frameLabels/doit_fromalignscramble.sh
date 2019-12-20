#!/bin/bash -xv

it=$1
let prevIt=$it-1

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`

desc=align-prior0.6.$dbname

./createDnnTrainingLabels.py --xmlalignments=`ls data/it${prevIt}.06.align-prior0.6.*/it${prevIt}.06.align-prior0.6.*.traceback-0.*.xml.gz | tr "\n" ","| sed -e 's,.$,\n,g'` --scrambleStream 0 --lexiconfile `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --states `grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --images `grep shared-train-imageFolder shared.config | cut -d"=" -f2 | tr -d " "`/  --corpus data/it0.train.corpus --output data/it${it}.train.framelabels.scrambled --removeSilenceFromPronunciations --useOne

./createDnnTrainingLabels.py --xmlalignments=`ls data/it${prevIt}.06.val.align-prior0.6.*/it${prevIt}.06.val.align-prior0.6.*.traceback-0.*.xml.gz | tr "\n" ","| sed -e 's,.$,\n,g'` --scrambleStream 0 --lexiconfile `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --states `grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --images `grep shared-val-imageFolder shared.config | cut -d"=" -f2 | tr -d " "`/  --corpus data/it0.val.corpus --output data/it${it}.dev.framelabels.scrambled --removeSilenceFromPronunciations --useOne

cp data/it${prevIt}.test.framelabels data/it${it}.test.framelabels

ln -s it${it}.dev.framelabels.scrambled data/it${it}.dev.framelabels 
ln -s it${it}.train.framelabels.scrambled data/it${it}.train.framelabels

