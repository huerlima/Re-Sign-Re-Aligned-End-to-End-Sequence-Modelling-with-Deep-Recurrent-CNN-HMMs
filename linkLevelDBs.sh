#!/bin/bash                
# link the leveldb to get around the lock that is created
# in this way multiple experiments can read from the same leveldb


to=data/leveldb_shuffle
shuffle=`grep shared-leveldb-folder-shuffle shared.config | cut -d"=" -f2| tr -d " "`

for set in train dev test; do
    mkdir -p $to/$set
    echo $set
    for file in `ls $shuffle/$set/*` ;do
        echo "ln -fs $file $to/$set/";
    done| grep -v LOCK | sh
done
for file in `ls $shuffle/` ;do
        echo "ln -fs $shuffle/$file $to/";
done|sh


to=data/leveldb
shuffle=`grep shared-leveldb-folder-noshuffle shared.config | cut -d"=" -f2| tr -d " "`

for set in train dev test; do
    mkdir -p $to/$set
    echo $set
        for file in `ls $shuffle/$set/*` ;do
                echo "ln -fs $file $to/$set/";
       done | grep -v "LOCK" |sh
done
for file in `ls $shuffle/` ;do
    echo "ln -fs $shuffle/$file $to/";
done|sh

