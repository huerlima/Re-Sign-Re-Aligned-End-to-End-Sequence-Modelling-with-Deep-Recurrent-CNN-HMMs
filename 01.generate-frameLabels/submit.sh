#!/bin/bash

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`
shared_feedforward_realigns=`grep shared-feedforward-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`
shared_feedforward_scrambled_realigns=`grep shared-feedforward-scrambled-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`


let start_scrambled_its=$shared_feedforward_realigns+1

it=$1
wait="-w it"$(($it-1))".align.val.$dbname,it"$(($it-1))".align.$dbname,$dbname.00.initial-lexicon-generation"

if [ $it -eq 1 ];then
   echo qsubmit -n it$it-init.$dbname $wait -m 2.0 -t 05:00:00 ./doit_linseg.sh $it 

elif [ $it -eq $start_scrambled_its ] && [ $shared_feedforward_scrambled_realigns -gt 0 ] ;then
    echo qsubmit -n it$it-init.$dbname $wait -m 2.0 -t 05:00:00 ./doit_fromalignscramble.sh $it

else
    echo qsubmit -n it$it-init.$dbname $wait -m 2.0 -t 05:00:00 ./doit_fromalign.sh $it
fi



