#!/bin/bash

if [ -z $1 ]; then
    echo "usage: $0 <iteration>"
    exit -1
fi

it=$1

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`

echo qsubmit -n it$it-generatePrior.$dbname -w it$it-dnnConvert.$dbname,it$it-dnnExtract.$dbname -m 1.0 -t 1:00:00 ./generatePrior.sh $it

