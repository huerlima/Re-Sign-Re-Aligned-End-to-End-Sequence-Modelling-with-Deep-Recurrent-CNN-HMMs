
# Re-Aligned Continuous Sign Language Recognition

This repository contains software to replicate the iterative realignment for continuous sign language recognition as described in:

O. Koller, S. Zargaran, and H. Ney. Re-Sign: Re-Aligned End-to-End Sequence Modelling with Deep Recurrent CNN-HMMs. In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pages 3416-3424, Honolulu, HI, USA, July 2017.

and also in

O. Koller, N. C. Camgoz, H. Ney, and R. Bowden. Weakly Supervised Learning with Multi-Stream CNN-LSTM-HMMs to Discover Sequential Parallelism in Sign Language Videos. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2019.

Please cite those works if this code helps you in your research.

## Installation

### Requirements & Dependencies

* SGE scheduler with CPU and GPU nodes
* RASR - Speech Toolkit https://www-i6.informatik.rwth-aachen.de/rwth-asr/
* Caffe - https://github.com/BVLC/caffe, with reverselayer.cpp reverselayer.cu and reverselayer.hpp from https://github.com/ChWick/caffe/blob/ctc/src/caffe/layers/reverse_layer.cpp
* cf -  cache management command line client. load balanced file caching on local harddisks, i6 internal. Can be replaced by a copy command
* leveldb - https://github.com/google/leveldb
* hdf5

### Setup

1. clone the repo
2. softlink the folder 'executables' to a folder where the RASR executables are located 
3. inside shared.config adjust links to the caffe binary and to the leveldb data sets

## Dataset Structures

Datasets used for training and evaluation consist of images only (videos currently not supported). 
The images that belong to one sequence are stored in a joint subfolder.
For each partition (train, development and test), text (\*.txt) files contain paths to those images and a dummy number separated by space.
Those files also determine the order in which the data is fed in for training.
A shuffled version (txt files and corresponding images in leveldb are shuffled) of the data set is needed for frame-wise training of the feed-forward networks.
A non shuffled version is needed for the LSTM training, as we train on full sequences there.
The images are converted into a leveldb dataset, which resides in the folder named by the partition they belong to (test, dev, train).

a) dataset having all images and sequences in order:
```
leveldb/
  train/
  dev/
  test/
  test.txt
  train.txt
  dev.txt
  train.mean
```
b) dataset with all images shuffled (on the frame level):
```
leveldb_shuffle/
  train/
  dev/
  test/
  test_shuffle.txt
  train_shuffle.txt
  dev_shuffle.txt
```
Only the train set is required to be shuffled. test and dev can be links to the unshuffled dataset.

train.mean contains the pixelwise mean stored as binary blob produced by caffe/tools/compute_image_mean.cpp
\*.txt files contain all images in the order as they are stored in the leveldb database. Each image is followed by a dummy class number (typically '0')
dev/ train/ test/ folders contain the leveldb files, those store the images which have been rescaled to 256x256 pixel. 
The data sets have been created with following command:
caffe/build/tools/convert_imageset path-to-images/ dev.txt /leveldb/dev -resize_height 256 -resize_width 256 -backend leveldb

## Create a LevelDB Dataset

Use the caffe tool convert_images. 
```
caffe/tools/convert_imageset point_to_image_folder/ train_shuffle.txt output/leveldb/train/ -resize_height 256 -resize_width 256 -backend leveldb
```
train_shuffle.txt is an image list. It is two column, space separated and contains the relative path to the images and a dummy label value. 

The feedforward networks are trained on shuffled data. Hence we need a shuffled train set: shuffle the image_list.txt and create a database in the leveldb_shuffle/ folder.
test and dev can be linked from the non-shuffled leveldb. The LSTM networks are trained with unshuffled data.


## Create a Corpus

RASR expects corpora in xml format. Use this tool to convert a plain text corpus into XML:
```
  ./tools/createcorpusFromFile.py -f plaintext.corpus CorpusName out.corpus
```
## Create a Language Model

The language model is used for decoding only. RASR supports different formats. In this context typically a count-based n-gram LM is used. This can be created with the SRILM toolkit.

## Training

start the training with start.sh
```
sh start.sh <start-iteration> <stop-iteration>
```
set start-iteration to 0 to initialise everything

Following steps will be executed:

* 00.initial-setup :arrow_right: one-time creation of lexicon and corpus files
* 01.generate-frameLabels :arrow_right: converts alignments to framelabel text files or performs a linear segmentation
* 02.traincaffe :arrow_right: converts text framelabels to hdf5 for training, initialises the model training and kicks off
* 03.extract-features :arrow_right: takes a trained model and produces framewise (log) posteriors that are stored in binary feature caches
* 05.generate-prior-mix :arrow_right: counts priors from framelabel text files
* 06.align-2stream :arrow_right: performs alignment using the framewise posteriors from the feature caches. writes out alignment cache

## Recognition
todo

## Debugging

### How to visualise the posterior caches
```
executables/archiver.linux-x86_64-standard --mode show data/it2.03.posteriors-0.dev/it2.0.train.cache.0000 phoenix2016-glosstranslation/29March_2010_Monday_tagesschau-8384/1
```
### How to visualise the alignment caches
```
executables/archiver.linux-x86_64-standard --mode show --type align data/it1.06.align-prior0.6.ph16-Pfh7-3stBLSTM-weigh05025025-Si/it1.align.06.align-prior0.6.ph16-Pfh7-3stBLSTM-weigh05025025-Si-2.cache.0001 phoenix2016-glosstranslation/29March_2010_Monday_tagesschau-8384/1
```
