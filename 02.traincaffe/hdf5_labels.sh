#!/bin/bash

# this script converts the text frame labels into hdf5 database 


it=$1

hdf5_dir='data/hdf5/'
mkdir -p $hdf5_dir
mkdir -p data/it$it.hdf5
for set in "train" "dev" "test";do echo $set;python makeShuffledList.py $set $it > data/it${it}.${set}_shuffle.framelabels;done
for set in "train" "dev" "test";do echo $set;python makeShuffledNonShuffledList.py $set $it > data/it${it}.${set}_noshuffle.framelabels;done

for shuffle in "_noshuffle" "_shuffle";do
	for set in "train${shuffle}" "test${shuffle}" "dev${shuffle}";do
		python hdf5_labels.py $it $set

		set_hdf5=$hdf5_dir/e2e_${set}.h5

		rm $set_hdf5

		ln -s $(fp ..)/data/it$it.hdf5/it${it}_${set}.h5 $set_hdf5

		echo $(fp ..)/${hdf5_dir}/e2e_${set}.h5 > $hdf5_dir/${set}.txt
	done
done
