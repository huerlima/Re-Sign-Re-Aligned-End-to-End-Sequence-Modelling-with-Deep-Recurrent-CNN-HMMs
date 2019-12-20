#!/bin/bash -xv

it=$1
let prevIt=$it-1

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`

desc=align-prior0.6.$dbname

# create train frame labels

for i in 0; do
fp data/it$prevIt.06.$desc/it$prevIt.align.06.${desc}-$i.cache.0* > data/it$prevIt.align.06.${desc}-$i.cache.bundle
done

./createDnnTrainingLabels.py --lexiconfile `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --states `grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'`  --images `grep shared-train-imageFolder shared.config | cut -d"=" -f2 | tr -d " "`/ --output data/it${it}.train.framelabels --alignmentcache data/it$prevIt.align.06.${desc}-0.cache.bundle --allophonefile data/it$prevIt.06.$desc/allophones.stream-0.0001 --ignoreMissingImages --ignoreDifferentLengths --useOne

# create val frame labels

for i in 0 ; do
fp data/it$prevIt.06.val.$desc/it$prevIt.align.06.val.${desc}-$i.cache.0* > data/it$prevIt.align.06.val.${desc}-$i.cache.bundle
done

./createDnnTrainingLabels.py --lexiconfile `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --states `grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'`  --images `grep shared-val-imageFolder shared.config | cut -d"=" -f2 | tr -d " "`/ --output data/it${it}.dev.framelabels --alignmentcache data/it$prevIt.align.06.val.${desc}-0.cache.bundle --allophonefile data/it$prevIt.06.$desc/allophones.stream-0.0001 --ignoreMissingImages --ignoreDifferentLengths --useOne


#copy test frame labels
cp data/it${prevIt}.test.framelabels data/it${it}.test.framelabels




