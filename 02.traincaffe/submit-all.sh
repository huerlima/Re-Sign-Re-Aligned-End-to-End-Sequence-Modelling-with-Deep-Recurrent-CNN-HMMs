#!/bin/bash -xv

it=$1

shared_feedforward_realigns=`grep shared-feedforward-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`
shared_feedforward_scrambled_realigns=`grep shared-feedforward-scrambled-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`

let start_blstm_its=$shared_feedforward_realigns+$shared_feedforward_scrambled_realigns+1

is_blstm=0
learningRate=`grep shared-standard-learningrate shared.config | cut -d '=' -f 2 | tr -d ' '`
batch_size_train=`grep shared-minibatch-size-train shared.config | cut -d '=' -f2 | tr -d " "`

if [ $it -ge  $start_blstm_its ];then
    is_blstm=1
    learningRate=`grep shared-blstm-learningrate shared.config | cut -d '=' -f 2 | tr -d ' '`
    batch_size_train=`grep shared-blstm-minibatch-size-train shared.config | cut -d '=' -f2 | tr -d " "`

fi

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`
meanTrainFile=`grep shared-mean-train-file shared.config | cut -d '=' -f2 | tr -d " "`
validateDNNLevelDB=dummy 
meanValFile=`grep shared-mean-validate-file shared.config | cut -d '=' -f2 | tr -d " "`

imageList=data/it${it}.train.framelabels


numImages=`cat $imageList | wc -l`

classcnt=$(nr=0;for f in $(grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " "); do states=`grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | awk '{if (NR-1=='$nr'){print $0}}'`;let nr=$nr+1;grep "<symbol>" $f | wc -l|awk '{states='$states';print ($1-1)*states+1}';done| tr "\n" ","| sed -e 's,\,$,\n,g')

validateDNNnumEntries=`grep shared-validateDNN-numEntries shared.config | cut -d '=' -f2 | tr -d " "|head -n1 | awk 'END{if ($0 == ""){print "0"}else{print $0}}'`


#for lr in 0.0001 0.0005 0.001 0.002 0.003 0.004; do

#if [ $it -lt 3 ]; then 
#maxEpochs=1
#stepLREpochs=1
##lrscheme="step"
#lrscheme="poly"
#weightDecay=0.0002
#else
maxEpochs=4
stepLREpochs=4
lrscheme="poly"
weightDecay=0.0002
#fi

for lr in $learningRate; do
./submit-net.sh $lr $(($numImages/$batch_size_train*$maxEpochs)) $lrscheme $weightDecay $(($numImages/$batch_size_train*$stepLREpochs)) 1 0.5 $imageList $validateDNNLevelDB $classcnt $meanTrainFile $meanValFile $numImages $validateDNNnumEntries $it |sh
done

#next job should wait
nextJob=it$it-dnnExtract.$dbname
nextJobShort=${nextJob:0:10}

for nextJobId in `qstat -u $USER | grep $nextJobShort |awk '{print $1}'`; do

if [ `qstat -j $nextJobId | grep job_name | cut -d ':' -f2  | tr -d " "` == $nextJob ];then
 echo qalter -hold_jid it$it-dnnTraintask.$dbname $nextJobId
      qalter -hold_jid it$it-dnnTraintask.$dbname $nextJobId

fi
done



