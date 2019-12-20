#! /bin/bash

source arch.sh
executable=./executables/acoustic-model-trainer.${executable}

it=`for i in $*; do echo $i; done | grep currIt | cut -d '=' -f2 | tr -d " "`
featureCache0=`grep shared-feature-val-cache-base-0 config/shared.config| cut -d '=' -f2 | tr -d " "`
featureCache1=`grep shared-feature-val-cache-base-1 config/shared.config| cut -d '=' -f2 | tr -d " "`

corpus=`grep shared-val-corpus config/shared.config| cut -d '=' -f2 | tr -d " "`
description=`for i in $*; do echo $i; done | grep description | cut -d '=' -f2 | tr -d " "`

stepIt=06.val
outp=it$it.$stepIt.$description
alignmentCacheBase0=it$it.align.$stepIt.$description-0.cache
alignmentCacheBase1=it$it.align.$stepIt.$description-1.cache
mkdir data/$outp                                                                                                                     

p=it$it.03.posteriors.dev
n=0000
featureCache0=data/$p/it$it.0.train.cache.$n
featureCache1=data/$p/it$it.1.train.cache.$n

alignmentCache0=/var/autofs/net/$(hostname)/${USER}/signlanguage/${dbname}/${alignmentCacheBase0}.${SGE_TASK_ID}
alignmentCache1=/var/autofs/net/$(hostname)/${USER}/signlanguage/${dbname}/${alignmentCacheBase1}.${SGE_TASK_ID}


mkdir -p $(dirname $alignmentCache0)
mkdir -p $(dirname $alignmentCache1)
if [ ! -d $(dirname $alignmentCache0) ]; then 
    alignmentCache0=/var/tmp/${USER}/signlanguage/${dbname}/${alignmentCacheBase0}.${SGE_TASK_ID}; 
    alignmentCache1=/var/tmp/${USER}/signlanguage/${dbname}/${alignmentCacheBase1}.${SGE_TASK_ID};

    mkdir -p $(dirname $alignmentCache0)
    mkdir -p $(dirname $alignmentCache1)

fi
rm -f $alignmentCache0 $alignmentCache1

echo "${executable}                                                 \
    --*.corpus.partition=${SGE_TASK_LAST}                           \
    --*.corpus.select-partition=${SGE_TASK_ID}                      \
    --*.corpus.recording-based-partition=true                       \
    --*.alignment-cache-0.path=${alignmentCache0}                     \
    --*.alignment-cache-1.path=${alignmentCache1}                     \
    --*.base-feature-extraction-cache-0.path=${featureCache0} \
    --*.base-feature-extraction-cache-1.path=${featureCache1} \
    --*.shared-corpus-file-base=${corpus} \
    --*.step=$stepIt \
    --*.it=$it \
    `for i in $*; do
        echo -n "$i ";
    done;`
"| sh
sleep 1
if [ $? -eq 0 -a -f $alignmentCache0 ]; then
    cf -cp $alignmentCache0 data/$outp/${alignmentCacheBase0}.${SGE_TASK_ID}
fi
if [ $? -eq 0 -a -f $alignmentCache1 ]; then
    cf -cp $alignmentCache1 data/$outp/${alignmentCacheBase1}.${SGE_TASK_ID}
fi
