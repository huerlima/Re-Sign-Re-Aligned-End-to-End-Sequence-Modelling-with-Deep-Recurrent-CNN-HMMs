#!/usr/bin/python
# author: jiseung shin, oscar koller
# date: 2017 02 03

# this python script uses a trained googlenet model to write the posteriors of all the training data into a sprint archive format file
# some sensitive assumptions are made:
# 1) data structure: we assume that the datastructure of the training data has the following format(which is also accepted by sprint):   CORPUS / SEGMENT / 1 / image_1, image_2, image_3, ..., imaage_N
# 2) we assume that the classes in classLabelList( image classlabel - textfile) the images are ordered in every segment, otherwise the resulting posteriors will be wrong!
# 3) the classlist corresponds to whatever classlabellist or leveldb database is specified in the net.prototxt
# 4) the TEST of net.prototxt is chosen to extract features

from SprintCache import FileArchive, FileArchiveBundle, FileInfo, MixtureSet, open_file_archive
import math
import sys
import numpy as np
import re


import progressbar
import os
args=sys.argv
print "\n".join(sys.argv)
from argparse import ArgumentParser
#import multiprocessing
import threading

global forWritingDict
#my_lock = threading.Lock()

def getOptions():
        arg_parser = ArgumentParser()
        arg_parser.add_argument("--net", help="the net structure, with which the training was performed")
        arg_parser.add_argument("--model", help="provide the caffe model, on which the posteriors should be calculated")
        arg_parser.add_argument("--classlist", help="image - classlabel textfile, structure: corpus/segment/(1)/image classlabel.")
        arg_parser.add_argument("--output", default="outs.features.cache", help="the name of the output cache file. If there are multiple layers dumped, you can provide a comma-separated list.")
        arg_parser.add_argument("--layer", default="loss3/SLclassifier", help="the name of the layer, where the posteriors are calculated, if there are multiple they may be comma-separated")
        arg_parser.add_argument("--path", default="/work/cv3/zargaran/caffe/caffe-reverselayer-2016_10_19/python/", help="specify the caffe python path [/work/cv3/zargaran/caffe/caffe-reverselayer-2016_10_19/python/]")
        arg_parser.add_argument("--partition", default="TEST", help="Set the caffe partition (TEST|TRAIN) [TEST]")
        arg_parser.add_argument("-v","--verbose",action="store_true", help="be verbose")
        args = arg_parser.parse_args()
        if len(sys.argv) == 1:
                arg_parser.print_help()
                sys.exit(1)
        return args

def writeToCache(featureList, segmentName, timeArray, featureCacheIndex):
        #global fas
        #global forWritingDict
        fas[featureCacheIndex].addAttributes(segmentName, len(featureList), len(timeArray))
        fas[featureCacheIndex].addFeatureCache(segmentName, np.array(featureList), timeArray)
        #with my_lock:
        #        forWritingDict.pop()

        
def main(argv):
        args = getOptions()
        
        # Make sure that caffe is on the python path:
        sys.path.append(args.path)

        import caffe


        # read the filenames and create a dictionary, which contains for each segment its including number of images
        if args.verbose:
                print "Reading test filenames..."


        # imagedict and runningSegments are used later to compare the caffe-net-output-file-names with the entries in the imageDict
        imageDict = dict()
        runningSegments = []

        # open class label textfile
        lines = open(args.classlist)

        # for each image in the classlabel file store only its corpus/segment/1/image to the images list 
        # and create a dictionary, in which for each segment you have the number of images.
        # This will be used in later functions, to controll the beginning and end of one segment and to check, if every images were really processed
        for line in lines:
                        
                line = "/" + line
                tempString = re.sub('/1/','/',line.strip('\n')).rsplit('/', 3)[1:-1]
                segmentname = '/'.join(tempString) + '/1'

                #else:
                # some formatting stuff to only store the relevant path information
                #        tempString = line.strip('\n').rsplit('/', 4)[1:5]
                #        segmentname = '/'.join(tempString[0:3])

                runningSegments.append(segmentname)

                # create the dictionary segment - number of containing images
                if segmentname not in imageDict:
                        imageDict[segmentname] = 0
                imageDict[segmentname] += 1

        # num of total images to process
        numImages = len(runningSegments)

        prevSegmentName = None
        # some auxiliary outputs
        print "the number of segments are: ", len(imageDict.keys())
        print "the total number of processed images are: ", numImages
        print " an example segment looks like this", imageDict.keys()[0]


        # Make sure that caffe is in the python path:
        caffe_root = '../'  # this file is expected to be in {caffe_root}/examples
        sys.path.insert(0, caffe_root + 'python')

        net = caffe.Net(args.net, args.model, getattr(caffe, args.partition))

        # GPU mode
        #caffe.set_device(int(gpu))
        caffe.set_mode_gpu()
        #caffe.set_device(int(gpu))
        batch_size = len(net.blobs[args.layer.split(',')[0]].data)

        if args.verbose:
                print "batch_size: ", batch_size

        iterOverMinibatch = int(math.ceil(float(numImages) / batch_size))  # number of images over batch size
        global numLayers
        numLayers = len(args.layer.split(','))
        layers = args.layer.split(',')
        global fas
        fas = []
        outnames = []
        for x in xrange(numLayers):
                if len(args.output.split(',')) == numLayers:
                        outnames.append(args.output.split(',')[x])
                else:
                        outnames.append(args.output.split(',')[0] + '.' + str(x))
                # create the archive file, if there is already one, delete and recreate it
                if os.path.exists(outnames[x]):
                        os.remove(outnames[x])
                fas.append(FileArchive(outnames[x], False))



        if args.verbose:
                print "number of npass is :", iterOverMinibatch

        # dictionary, which entries will be written in the archive format, its structure is: segment - [list of posteriors for the images in one segment]
        # IMPORTANT!!!!!    here we assume, that the images are in correct incrementing order!!!
        global forWritingDict
        forWritingDict = []
        threads = []
        for x in xrange(numLayers):
                forWritingDict.append({})
                threads.append(None)
        if not args.verbose:
                progBar = progressbar.progressBar(0, iterOverMinibatch, 77)
                FileCounter = 0
                progBar.draw()        
        for i in range(iterOverMinibatch):
                if args.verbose:
                        print "processing unit is: " + str(i)
                else:
                        FileCounter += 1
                        progBar.updateAmount(FileCounter)   
                        progBar.draw() 

                net.forward()  # call once for allocation
                for j in range(len(net.blobs[args.layer.split(',')[0]].data)):
                        imgNum = i * batch_size + j

                        #for layer in args.layer.split(','):  # deal with comma-separated list
                        #        feat.append(net.blobs[layer].data[j].tolist())

                        # get the segmentname
                        if imgNum >= len(runningSegments):
                            print "imgNum", imgNum, "len(runningSegments)", len(runningSegments)
                            break
                        segmentName = runningSegments[imgNum]
                        if args.verbose:
                                print "segment Name", segmentName, "numImages in Segment", imageDict[segmentName]

                        #if segmentname is not found in the forWriting Dictionary make a new entry
                        if segmentName not in forWritingDict[0]:
                                for x in xrange(numLayers):
                                        forWritingDict[x][segmentName] = []
                                        #[ net.blobs[layers[x]].data[j] ]
                        #else:
                                # then add the feature into the featurelist
                        for x in xrange(numLayers):
                                forWritingDict[x][segmentName].append(net.blobs[layers[x]].data[j].tolist())
                                        #print ""
                                        #print forWritingDict[x][segmentName]
                                        #sys.exit()
                        # then check, if the entries are full, if this is full, write it into archive format and pop the entry from dict

                        # check if the one segment has been filled completely, if this is the case, write it in the Sprint archive format
                        # print imageDict[segmentName], len(forWritingDict[segmentName]), segmentName, runningSegments[imgNum]
                        sequenceTotImages = imageDict[segmentName]

                        if len(forWritingDict[0][segmentName]) == sequenceTotImages:    
                                time = np.array([[0.0, 0.04]])
                                t = np.array(time)
                                for step in range(1,sequenceTotImages):
                                        time = time + 0.04
                                        t = np.append(t,time,axis=0)
                                                
                                for x in xrange(numLayers):
                                        #f = np.array(forWritingDict[x][segmentName])

                                        # if args.verbose:
                                        #        print len(f)
                                        #        print len(t)
                                        if threads[x] is not None:
                                                threads[x].join()
                                                forWritingDict[x].pop(prevSegmentName)
                                        threads[x] = threading.Thread(target=writeToCache, args=(forWritingDict[x][segmentName], segmentName, t, x))
                                        #threads[x] = multiprocessing.Process(target=writeToCache, args=(forWritingDict[x][segmentName], segmentName, t, x))
                                        threads[x].start()
                                        # fas[x].addAttributes(segmentName, len(forWritingDict[x][segmentName]), len(t))
                                        # fas[x].addFeatureCache(segmentName, np.array(forWritingDict[x][segmentName]), t)

                                        # delete the entries from forWritingDict and imageDict only needed for debugging
                                if prevSegmentName is not None:
                                        imageDict.pop(prevSegmentName)
                                # forWritingDict[x].pop(segmentName)
                                # imageDict.pop(segmentName)

                                #debug!
                                #for x in xrange(numLayers):
                                #        fas[x].finalize()
                                #exit()
                                prevSegmentName = segmentName


        # at the end write everythin in the sprint archive format

        for thread in threads:
                if thread is not None:
                        thread.join()
        for x in xrange(numLayers):
                fas[x].finalize()
        print ""
        print "remaining entries:", len(imageDict)
        for seg in imageDict:
            print seg 
                
if __name__ == "__main__":
    main(sys.argv)
