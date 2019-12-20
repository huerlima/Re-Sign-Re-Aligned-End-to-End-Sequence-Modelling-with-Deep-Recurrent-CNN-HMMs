#!/bin/bash 
#-xv

if [ -z ${15} ]; then
    echo "usage: $0 <base_lr> <max_iter> <lr_policy:poly> <weight_decay> <step> <lastLayerLR> <gamma> <levelDBTrain.bundle> <levelDBTest.bundle> <number of lastlayer Outputs> <trainMeanFile> <testMeanFile> <num_train_samples> <num_test_samples> <iteration>"
    exit -1
fi

base_lr=$1
lr_policy=$3
max_iter=$2
weight_decay=$4
step=$5
lastLayerLR=$6
gamma=$7
leveldbtrain=$8
leveldbtest=$9
numOutputs=${10}
trainMeanFile=${11}
testMeanFile=${12}
numTrainSamples=${13}
numTestSamples=${14}
it=${15}


shared_feedforward_realigns=`grep shared-feedforward-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`
shared_feedforward_scrambled_realigns=`grep shared-feedforward-scrambled-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`


let start_blstm_its=$shared_feedforward_realigns+$shared_feedforward_scrambled_realigns+1

is_blstm=0
batch_size_test=`grep shared-minibatch-size-val shared.config | cut -d '=' -f 2 | tr -d ' '`
batch_size_train=`grep shared-minibatch-size-train shared.config | cut -d '=' -f2 | tr -d " "`

if [ $it -ge  $start_blstm_its ];then
    is_blstm=1
    batch_size_test=`grep shared-blstm-minibatch-size-val shared.config | cut -d '=' -f 2 | tr -d ' '`
    batch_size_train=`grep shared-blstm-minibatch-size-train shared.config | cut -d '=' -f2 | tr -d " "`
fi

description=it$it.lr${base_lr}-maxit${max_iter}-policy${lr_policy}-weightdecay${weight_decay}-step${step}-lastLayerLR-${lastLayerLR}-gamma${gamma}

mkdir data/$description

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`
displaysperepoch=20
testsperepoch=4
snapshotsperepoch=4

trainIter=`echo $numTrainSamples|awk '{printf "%d", $1/'$batch_size_train'/'$displaysperepoch'}'|awk '{printf "%d", $1*4}'`
display=`echo $numTrainSamples|awk '{printf "%d", $1/'$batch_size_train'/'$displaysperepoch'}'`
testing=`echo $numTrainSamples|awk '{printf "%d", $1/'$batch_size_train'/'$testsperepoch'}'`
snapshotting=`echo $numTrainSamples|awk '{printf "%d", $1/'$batch_size_train'/'$snapshotsperepoch'}'`


testIter=`echo $numTestSamples|awk '{printf "%d", $1/'$batch_size_test'}'`

echo "net: \"submit-net.prototxt\"" >  data/$description/solver.prototxt
cnt=0;
for num in $( grep shared-validateDNN-numEntries shared.config | cut -d '=' -f2 | tr -d " " ); do
#echo "test_iter: "$(($num/$batch_size_test)) >> data/$description/solver.prototxt
#echo "test_state: { stage: \""$cnt"\" }" >> data/$description/solver.prototxt
let cnt=$cnt+1
done
#num=`cat data/it$it.011.alignment-.0-54HighlevelFeaturesLast13OnlyDeriv-train.cache.0010-it$it/dev.classes.it$it.c3d.absolutePath | wc -l`
echo "test_iter: "$testIter >> data/$description/solver.prototxt
echo "test_state: { stage: \""$cnt"\" }" >> data/$description/solver.prototxt
echo "test_interval: $testing
test_initialization: false
display: $display
average_loss: 40
base_lr: $base_lr #0.0001
lr_policy: \"${lr_policy}\"
power: 0.5
max_iter: $max_iter #50000
stepsize: $step
gamma: $gamma
momentum: 0.9
weight_decay: $weight_decay #0.0002
snapshot: $snapshotting
snapshot_prefix: \"bvlc_googlenet_$description\"
solver_mode: GPU
#iter_size: 20
#type: \"Adam\"
" >>  data/$description/solver.prototxt

currdir=`pwd`
echo pwd
echo "cd data/$description"


target_machine=""
    if [ $it -ge $start_blstm_its ]; then
        target_machine="-a GPU-1080,GPU-TITAN"
    fi
echo qsubmit -n it$it-dnnTraintask.$dbname -w it$it-generateImageList.$dbname $target_machine -gpu -m 10 -t 155:59:00 $currdir/trainNet.sh `readlink -f $leveldbtrain` `readlink -f $leveldbtest` $lastLayerLR $numOutputs $trainMeanFile $testMeanFile $it


echo "cd -"
echo pwd
