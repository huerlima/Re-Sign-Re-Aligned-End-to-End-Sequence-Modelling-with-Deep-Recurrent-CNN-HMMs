#!/bin/bash -xv

start=$1
end=$2

if [ -z "$2" ]; then

    echo "call me like this: start.sh <start-iteration> <stop-iteration>"
    exit 0
fi

shared_feedforward_realigns=`grep shared-feedforward-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`
shared_feedforward_scrambled_realigns=`grep shared-feedforward-scrambled-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`
shared_blstm_realigns=`grep shared-blstm-realigns shared.config | cut -d '=' -f 2 | tr -d ' '`

let start_scrambled_its=$shared_feedforward_realigns+1
let total_scrambled_its=$shared_feedforward_realigns+$shared_feedforward_scrambled_realigns
let start_blstm_its=$total_scrambled_its+1
let total_blstm_its=$total_scrambled_its+$shared_blstm_realigns

for it in $(seq $start $end); do 

if [ $it -eq 0 ]; then
    sh linkLevelDBs.sh
    cd 00.initial-setup
    sh init-feedforward.sh
    cd ..
    continue
fi

echo "submitting it "$it

cd 01.generate-frameLabels/
    ./submit.sh $it |sh
cd ..

cd 02.traincaffe
./submit.sh $it |sh
cd ..

cd 03.extract-features/
./submit.sh $it |sh
cd ..

cd 05.generate-prior-mix/
./submit.sh $it |sh
cd ..

cd 06.align-2stream/
./submit.sh $it |sh
cd ..
done
