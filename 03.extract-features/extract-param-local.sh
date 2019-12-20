#!/bin/bash

if [ -z "$4" ]; then

echo "usage: submit.sh <iterationnumber> <model> <outputPath> <imageList>"
exit

fi

export SGE_TASK_ID=`printf %04d ${SGE_TASK_ID}`

it=$1
model=$2
p=$3
imageList=$4

# load shared configs
dbname=`grep shared-experiment-name shared.config | cut -d '=' -f2 | tr -d " "`
batchsize=`grep shared-minibatch-size-train shared.config | cut -d '=' -f2 | tr -d " "`
caffeExecutables=`grep shared-caffe-executables shared.config | cut -d '=' -f2 | tr -d " "`

# set environment to contain everything needed for caffe and cuda:
# glog, cuda, leveldb, caffe, opencv, mkl, snappy-1
#export PYTHONPATH="/u/koller/work/src/signlanguage/pylib/"
export LD_LIBRARY_PATH="/u/koller/lib16.04/:/work/cv2/koller/software/glog/.libs/:/usr/lib/x86_64-linux-gnu/:/usr/local/cuda-8.0/lib64/:/lib/x86_64-linux-gnu/:/work/cv2/koller/software/leveldb/out-shared/:/u/koller/lib-caffe/:/work/cv3/zargaran/software/cudnn-8.0-linux-x64-v5.1/lib64/:/work/cv2/koller/software/opencv/opencv-2.4.13-16.04/build/lib/:/usr/local/intel.15/mkl/lib/intel64/:/work/cv2/forster/software/snappy-1.1.2/jens-install/lib/"

# activate python environment that contains a working pycaffe
source /work/cv2/koller/software/python-envs/activitynet-16.04/bin/activate
export PKG_CONFIG_PATH=/usr/lib/pkgconfig/

modelPath=$(echo $model | rev | cut -d"/" -f2- | rev) 
echo $modelPath/submit-net.protoxt

python train2extractPrototxt.py --path $caffeExecutables/python/ --prototxt $modelPath/submit-net.prototxt --outproto tmp.$p.general.prototxt --hdfsource=data/hdf5/${imageList}_noshuffle.txt --datasource=data/leveldb/$imageList

cat tmp.$p.general.prototxt | sed -e 's,batch_size: .*$,batch_size: '$batchsize',g' > tmp.$p.prototxt

n=0001
mkdir data/$p

featCache0=/var/autofs/net/$(hostname)/${USER}/signlanguage/${dbname}/$p/it$it.0.train.cache.${SGE_TASK_ID}
#featCache1=/var/autofs/net/$(hostname)/${USER}/signlanguage/${dbname}/$p/it$it.1.train.cache.${SGE_TASK_ID}


mkdir -p $(dirname $featCache0)
#mkdir -p $(dirname $featCache1)
if [ ! -d $(dirname $featCache0) ]; then
        featCache0=/var/tmp/${USER}/signlanguage/${dbname}/$p/it$it.0.train.cache.${SGE_TASK_ID}
 #       featCache1=/var/tmp/${USER}/signlanguage/${dbname}/$p/it$it.1.train.cache.${SGE_TASK_ID}
        mkdir -p $(dirname $featCache0)
  #      mkdir -p $(dirname $featCache1)
fi
rm -f $featCache0 #$featCache1




cmd="python writeCaffePosteriorInArchiveFormat.py --net tmp.$p.prototxt --classlist data/leveldb/$imageList.txt --model $model --layer loss3/loss3-0 --output $featCache0 --path $caffeExecutables/python/"
echo $cmd
echo $cmd | sh

sleep 1
if [ $? -eq 0 -a -f $featCache0 ]; then
        cf -cp $featCache0 data/$p/it$it.0.train.cache.${SGE_TASK_ID}
fi
#if [ $? -eq 0 -a -f $featCache1 ]; then
#        cf -cp $featCache1 data/$p/it$it.1.train.cache.${SGE_TASK_ID}
#fi

