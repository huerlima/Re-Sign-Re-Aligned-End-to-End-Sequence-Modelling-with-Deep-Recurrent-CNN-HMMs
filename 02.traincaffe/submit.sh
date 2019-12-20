#!/bin/bash

if [ -z $1 ]; then
    echo "usage: $0 <iteration>"
    exit -1
fi

it=$1

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`

echo qsubmit -n it$it-dnnTrain.$dbname -w it$it-generateImageList.$dbname,it$it-init.$dbname -m 1.0 -t 3:10:00 ./submit-all.sh $it




