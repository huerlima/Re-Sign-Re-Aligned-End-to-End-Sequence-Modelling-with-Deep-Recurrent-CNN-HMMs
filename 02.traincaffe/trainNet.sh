#!/bin/bash -xv

if [ -z $4 ]; then
    echo "usage: $0 <abs:levelDBTrain.bundle> <abs:levelDBTest.bundle> <lastLayerLR> <numOutputs> <trainMeanFile> <testMeanFile> <it>"
    exit -1
fi

leveldbtrain=$1
leveldbtest=$2
lastLayerLR=$3

lastLayerLR1=$((1*$lastLayerLR))
lastLayerLR2=$((2*$lastLayerLR))

numOutPuts=`echo $4| cut -d"," -f1`
numOutPuts1=`echo $4| cut -d"," -f2`

trainMeanEntry=$5
testMeanEntry=$6
it=$7
localDir=`dirname $0`

# show directory for debugging
echo `pwd`
cd $localDir

# create hdf5 lists
./hdf5_labels.sh $it

# show directory for debugging
echo `pwd`
cd -
echo `pwd`

# set env variables
export PYTHONPATH=$PYTHONPATH":/work/cv2/python/lib/python2.7/site-packages"
export PKG_CONFIG_PATH=""
export LD_LIBRARY_PATH="/usr/lib/x86_64-linux-gnu/:/usr/local/cuda-8.0/lib64/:/work/cv2/imagelibs/lib/:/work/cv2/forster/software/glog-0.3.3/jens-install/lib:/work/cv3/zargaran/software/opencv-2.4.13/build/lib/:/work/cv3/zargaran/software/cudnn-8.0-linux-x64-v5.1/lib64/:/usr/local/intel.15/mkl/lib/intel64/"

# get shared settings
caffeExecutables=`grep shared-caffe-executables $localDir/shared.config | cut -d '=' -f2 | tr -d " "`
dataDir=`echo $localDir| sed -e 's,/[^/]*$,,'`
testminibatchsize=`grep shared-minibatch-size-val $localDir/shared.config | cut -d '=' -f2 | tr -d " "`
trainminibatchsize=`grep shared-minibatch-size-train $localDir/shared.config | cut -d '=' -f2 | tr -d " "`
googleNetPretrained=`grep shared-googleNet-pretrained $localDir/shared.config | cut -d '=' -f2 | tr -d " "`
shared_feedforward_realigns=`grep shared-feedforward-realigns $localDir/shared.config | cut -d '=' -f 2 | tr -d ' '`
shared_feedforward_scrambled_realigns=`grep shared-feedforward-scrambled-realigns $localDir/shared.config | cut -d '=' -f 2 | tr -d ' '`
let start_lstm_its=$shared_feedforward_realigns+$shared_feedforward_scrambled_realigns
if [ $it -gt $start_lstm_its ];then
   echo "BLSTMs are added to network structure"
   isFeedForward=0
   top="top: \"cont\""
   source="source: \"../hdf5/dev_noshuffle.txt\""
   targetProto=submit-net.prototxt_GN2BLSTM
   testminibatchsize=`grep shared-blstm-minibatch-size-val $localDir/shared.config | cut -d '=' -f 2 | tr -d ' '`
   trainminibatchsize=`grep shared-blstm-minibatch-size-train $localDir/shared.config | cut -d '=' -f 2 | tr -d ' '`
else
   echo "network is feedforward only"
   isFeedForward=1
   top="#top: \"cont\""
   source="source: \"../hdf5/dev_shuffle.txt\""
   targetProto=submit-net.prototxt_GN
fi

# create training network scheme
cnt=0
echo "name: \"GoogleNet\"" > tmp.submit.proto

for leveldbtest in "../it${it}.val.framelabels.short" ; do
    let cnt=$cnt+1
    if [ -d $leveldbtest ]; then

      fp $leveldbtest/* > tmp.test.bundle
      mkdir -p /var/tmp/koller/$JOB_ID/$leveldbtest
      cf -cp --noregister tmp.test.bundle /var/tmp/koller/$JOB_ID/$leveldbtest
      testLocal=/var/tmp/koller/$JOB_ID/$leveldbtest
    else
       testLocal=$leveldbtest
    fi

    localDir=`dirname $0`
    dataDir=`echo $localDir| sed -e 's,/[^/]*$,,'`

    if [ $cnt -eq 1 ];then
        stage=""
    else
        stage="stage: \"$cnt\""
    fi


    echo "
    layer {
      name: \"data\"
      type: \"Data\"
      top: \"data\"
      top: \"label1\"
      include {
        phase: TEST
            "$stage"
      }
      transform_param {
        mirror: false
        crop_size: 224
        mean_file: \"$testMeanEntry\"
      }
      data_param {
        source: \"../leveldb/dev/\"
        batch_size: "$testminibatchsize"
    #    new_height: 256
    #    new_width: 256
      }
    }
    layer {
      name: \"data\"
      type: \"HDF5Data\"
      top: \"label-0\"
      "$top"
      include { phase: TEST }
      hdf5_data_param {
        "$source"
        batch_size: "$testminibatchsize"
      }
    }" >> tmp.submit.proto

    let cnt=$cnt+1
done



#check if leveldbs are actually folders
if [ -d $leveldbtrain ]; then
    fp $leveldbtrain/* > tmp.train.bundle
    mkdir -p /var/tmp/koller/$JOB_ID/$leveldbtrain
    cf -cp --noregister tmp.train.bundle /var/tmp/koller/$JOB_ID/$leveldbtrain
    trainLocal=/var/tmp/koller/$JOB_ID/$leveldbtrain
else
    trainLocal=$leveldbtrain
fi

#fill in layer details to neural network scheme
cat tmp.submit.proto <(cat $localDir/$targetProto| sed -e 's,batch_size:.*,batch_size: '$trainminibatchsize',') | sed -e 's,lastlearningrateparam1Entry,'$lastLayerLR1',' -e 's,lastlearningrateparam2Entry,'$lastLayerLR2',' -e 's,trainleveldbEntry,'$trainLocal',' -e 's,testleveldbEntry,'$testLocal',' -e 's,numoutputparam-0,'$numOutPuts',g' -e 's,numoutputparam-1,'$numOutPuts1',g' -e 's,numoutputparam-2,'$numOutPuts2',g' -e 's,numoutputparam-3,'$numOutPuts3',g'  -e 's,testmeanEntry,'$testMeanEntry',' -e 's,trainmeanEntry,'$trainMeanEntry',' > submit-net.prototxt 

caffemodelinit=""
if [ "$it" -eq 1 ];then
   caffemodelinit="-weights="$googleNetPretrained
#elseif [ "$it" -eq 1 ]; then
#    #ffExp=`grep shared-feedforward-exp $localDir/shared.config | cut -d '=' -f 2 | tr -d ' ' `
#    modelPath=$ffExp/data/it4.lr0*
#    lastModel=`ls -tr $modelPath/*.caffemodel | tail -n1`
#    caffemodelinit="-weights="$lastModel
elif [ "$it" -gt 1 ];then
    caffemodelinit="-weights="$(ls -tr ../it$(($it-1)).lr*/bvlc*.caffemodel | tail -n1 | sed -e 's,data,..,g')
fi

$caffeExecutables/build/tools/caffe train -solver=solver.prototxt $caffemodelinit
