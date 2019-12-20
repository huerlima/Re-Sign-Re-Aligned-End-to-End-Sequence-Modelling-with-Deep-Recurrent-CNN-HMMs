#!/bin/bash

if [ -z "$1" ]; then

echo "usage: submit.sh <iterationnumber>"
exit

fi

it=$1

dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`

echo qsubmit -n it$it-dnnExtract.$dbname -w it$it-dnnTrain.$dbname,it$it-dnnTraintask.$dbname,it$it.mouthGNshortC3D -gpu -m 22 -t 72:00:00 ./doit.sh $it

