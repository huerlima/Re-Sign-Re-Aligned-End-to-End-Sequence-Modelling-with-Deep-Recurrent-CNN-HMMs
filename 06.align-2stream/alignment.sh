#! /bin/bash

source arch.sh

executable=./executables/acoustic-model-trainer.${executable}

it=`for i in $*; do echo $i; done | grep currIt | cut -d '=' -f2 | tr -d " "`
featureCache0=`grep shared-feature-train-cache-base-0 config/shared.config| cut -d '=' -f2 | tr -d " "`
featureCache1=`grep shared-feature-train-cache-base-1 config/shared.config| cut -d '=' -f2 | tr -d " "`

corpus=`grep shared-train-corpus config/shared.config| cut -d '=' -f2 | tr -d " "`
description=`for i in $*; do echo $i; done | grep description | cut -d '=' -f2 | tr -d " "`

stepIt=06
outp=it$it.$stepIt.$description
alignmentCacheBase0=it$it.align.$stepIt.$description-0.cache
mkdir data/$outp


p=it$it.03.posteriors
n=0000
featureCache0=data/$p/it$it.0.train.cache.$n

# write alignment cache to a local temp location

alignmentCache0=/var/autofs/net/$(hostname)/${USER}/signlanguage/${dbname}/${alignmentCacheBase0}.${SGE_TASK_ID}


mkdir -p $(dirname $alignmentCache0)
mkdir -p $(dirname $alignmentCache1)
if [ ! -d $(dirname $alignmentCache0) ]; then 
    alignmentCache0=/var/tmp/${USER}/signlanguage/${dbname}/${alignmentCacheBase0}.${SGE_TASK_ID}; 

    mkdir -p $(dirname $alignmentCache0)
    mkdir -p $(dirname $alignmentCache1)

fi
rm -f $alignmentCache0 $alignmentCache1

echo "${executable}                                                 \
    --*.corpus.partition=${SGE_TASK_LAST}                           \
    --*.corpus.select-partition=${SGE_TASK_ID}                      \
    --*.corpus.recording-based-partition=true                       \
    --*.alignment-cache-0.path=${alignmentCache0}                     \
    --*.base-feature-extraction-cache-0.path=${featureCache0} \
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
