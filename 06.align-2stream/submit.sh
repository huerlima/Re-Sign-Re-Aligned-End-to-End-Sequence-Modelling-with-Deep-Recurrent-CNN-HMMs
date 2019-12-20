#!/bin/bash

if [ -z $1 ]; then
    echo "usage: $0 <iteration>"
    exit -1
fi

it=$1

dbname=`grep shared-experiment-name config/shared.config | cut -d '=' -f2 | tr -d " "`

wait="-w it$(($it))-generatePrior.$dbname,it$it-dnnConvert.$dbname,it$it-dnnExtract.$dbname"

echo qsubmit -nomail -m 4.0 $wait -t 0:30:00 -n it$it.align.$dbname -j 1-5  ./alignment.sh --config=config/alignment.config --*.description=align-prior0.6.$dbname --currIt=$it
echo qsubmit -nomail -m 4.0 $wait -t 0:30:00 -n it$it.align.val.$dbname -j 1  ./alignmentVal.sh --config=config/alignment.config --*.description=align-prior0.6.$dbname --currIt=$it

