#!/bin/bash -xv

if [ -z $1 ]; then
    echo "usage: $0 <iteration>"
    exit -1
fi

it=$1

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`
nr=0

for lex in `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " "`; do
    states=`grep shared-states-$nr shared.config | cut -d"=" -f2 | tr -d " "`
    classcnt=`cat $lex | grep "<symbol>"|wc -l |awk '{states='$states';print ($1-1)*states+1}'`
    for i in $(seq 0 1 $(($classcnt-1)));do echo "$i $i";done > data/hybrid-featurescorer.mapping-mix2dnn-$nr.txt
    mappingLength=`cat data/hybrid-featurescorer.mapping-mix2dnn-$nr.txt | wc -l`

    imageList=data/it$it.train.framelabels

    echo $classcnt | awk 'BEGIN{srand();}{featdim=1;mixcnt=$1;print "#Version: 2.0";print "#CovarianceType: DiagonalCovariance"; print featdim" "mixcnt" "mixcnt" "mixcnt" "mixcnt;for (i=0;i<mixcnt;i++){printf "1 %d %0.4f\n", i,log(10);}for (i=0;i<mixcnt;i++){print i" "i;} for (i=0;i<mixcnt;i++){printf "%d ",featdim;for (f=0;f<featdim;f++){printf "%0.5f ",0.5}printf "\n";}for (i=0;i<mixcnt;i++){printf " %d ",featdim;for (f=0;f<featdim;f++){printf "%0.5f 1 ",0.5}printf "\n"}}' > data/generic.mixture-file.pms

    cat <(head -n 3 data/generic.mixture-file.pms)  <(cat data/hybrid-featurescorer.mapping-mix2dnn-$nr.txt <(cat $imageList |  awk '{print $NF}' | cut -d"," -f$(($nr+1))|sort | uniq -c| sort -k2 -g | awk '{print $0;num=$2}END{clscnt='$classcnt';if (num<clscnt-1){print "10 "clscnt-1}}' ) | awk 'BEGIN{cnt=0}{maplen='$mappingLength';if (NR<=maplen){map[$2]=$1}else{if ($2!=cnt){miss=$2-cnt;for (i=0;i<miss;i++){print "0.1 "cnt" "map[cnt];cnt+=1}}print $1" "$2" "map[$2];cnt+=1}}'| awk '{print 1" "NR-1" "log($1)}') |  awk 'BEGIN{srand();featdim=1;mixcnt='$classcnt'}{print $0}END{for (i=0;i<mixcnt;i++){print i" "i;} for (i=0;i<mixcnt;i++){printf "%d ",featdim;for (f=0;f<featdim;f++){printf "%0.5f ",0.5}printf "\n";}for (i=0;i<mixcnt;i++){printf " %d ",featdim;for (f=0;f<featdim;f++){printf "%0.5f 1 ",0.5}printf "\n"}}' > data/it$it.priors-$nr.pms

    ./executables/acoustic-model-trainer.linux-x86_64-standard --action=convert-mixture-set-to-mixture-set-estimator --*.mixture-set-trainer.file=data/it$it.priors-$nr.pms --*.new-mixture-set-file=data/it$it.priors-$nr.mix  --*.log.channel=stdout

    let nr=$nr+1
done
















