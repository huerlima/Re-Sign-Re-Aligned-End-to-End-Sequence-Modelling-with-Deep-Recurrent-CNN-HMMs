#!/bin/bash -xv

it=$1

modelPath=data/it$it.lr0*
lastModel=`ls -tr $modelPath/*.caffemodel | tail -n1`
outputFolder=it$it.03.posteriors

#sh linkLevelDBs.sh 

./extract-param-local.sh $it $lastModel $outputFolder.dev dev
./extract-param-local.sh $it $lastModel $outputFolder.test test
./extract-param-local.sh $it $lastModel $outputFolder train



