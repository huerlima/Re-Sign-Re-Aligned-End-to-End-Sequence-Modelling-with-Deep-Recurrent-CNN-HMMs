#!/usr/bin/python
# author: jiseung shin, oscar koller
# date: 2016 12 14

# This script is used to create a class label data of the structure:
# path_to_image/image_name classlabel.
# input:
#   alignent cache,
#   allophone file,
#   lexicon file,
#   output file name,
#   number of states (per symbol) of the used hmm,
#   specification of directory structure (1ed or not)

from SprintCache import open_file_archive

import sys
from os import listdir
import os, glob
from os.path import isfile, join
from handlers import LexiconHandler, CorpusHandler
from xml.sax import make_parser
import xml.sax
from argparse import ArgumentParser
import time
import math
import progressbar
import copy
import gzip
import numpy as np

def main():
    # argument parser to read the crucial arguments:
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--images", default="/work/cv3/shin/ph16/images/PH16_FF/", help="path to the image files")
    arg_parser.add_argument("--alignmentcache", help="alignment cache file (can optionally be a comma-separated sequence, for multiple caches)")
    arg_parser.add_argument("--allophonefile", help="allophone file  (can optionally be a comma-separated sequence, for multiple files)")
    arg_parser.add_argument("--lexiconfile", help="Lexicon file  (can optionally be a comma-separated sequence, for multiple files)")
    arg_parser.add_argument("--states", default="3", help="number of states")
    arg_parser.add_argument("--output", default="imageLabeltxt", help="name of the output file")
    arg_parser.add_argument("--useOne", action="store_true", help="in some image data structure a 1 can be contained")
    arg_parser.add_argument("--corpus", help="If no alignment cache is available give the number of states and it will create a linear aligned class labeling output")
    arg_parser.add_argument("--borderSilence",type=int, default=0, help="Instead of a ratio use an absolute number of silence frames at the beginning and end of a segment.")
    arg_parser.add_argument("--beginSilence",type=int, default=0, help="Instead of a ratio use an absolute number of silence frames at the beginning of a segment. [0]")
    arg_parser.add_argument("--endSilence",type=int, default=0, help="Instead of a ratio use an absolute number of silence frames at the end of a segment. [0]")
    arg_parser.add_argument("--midSilence",type=int, default=0, help="Absolute number of silence frames between words. [0]")
    arg_parser.add_argument("--outputC3Dstyle",action="store_true", help="Outputs files compatible with C3D (3dconv by facebook) training <string_path> <starting_frame> <label1> ... <labelN>")
    arg_parser.add_argument("--C3DclipLength",type=int, default=16, help="Set the C3D clip length")
    arg_parser.add_argument("--ignoreDifferentLengths",action="store_true", help="Ignore mismatch in number of alignments and images (truncate the sequence when this happens)")
    arg_parser.add_argument("--ignoreMissingImages",action="store_true", help="Ignore if image-folders are not present.")
    arg_parser.add_argument("--imageExtension",default="*.png", help="Set the image extension of images in the image folder [*.png].")
    arg_parser.add_argument("--scrambleStream", type=int, help="Scramble all available pronunciations for a given stream.")
    arg_parser.add_argument("--xmlalignments", help="xml alignment file for stream to be scrambled")
    arg_parser.add_argument("--subunits", action="store_true", help="Process subunits.")
    arg_parser.add_argument("--removeSilenceFromPronunciations", action="store_true", help="Remove silence from pronunciation prior to generating frame alignments.")
    arg_parser.add_argument("--maximum_pronunciation_number_to_consider",type=int, help="Set the maximum number of Pronunciations to take into consideration when generating linear segmentation")

    arg_parser.add_argument("-v","--verbose",action="store_true", help="be verbose")
    global args
    args = arg_parser.parse_args()
    if len(sys.argv) == 1:
        arg_parser.print_help()
        sys.exit(1)

# if option scrambled is set, read in xml.gz alignments and perform a linear segmentation, scrambling through all available pronunciations
    if args.scrambleStream != None:
        assert args.states
        assert args.xmlalignments
        generateScrambledLinearAlignmentV2(args)

# if no alignment cache is given, assume linear alignment and produce the class labeling according to the corpus, imagefile and states 
    elif not args.alignmentcache:
        if args.states:
            generateLinearAlignedClassLabel(args)

# otherwise we assume, that an alignment cache is given, so produce the class labels based on the alignment cache, lexicon and  allophone file
    else:   
        generateClassLabel(args)

def generateScrambledLinearAlignment(args):
    # need to encode utf8
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # read the corpus
    corpusfile = args.corpus
    parser = make_parser()
    corpus = CorpusHandler(encoding="UTF-8",includedir=corpusfile )
    parser.setContentHandler(corpus)
    parser.parse(corpusfile)

    corpus_name = corpus.name

    xmlaligns={}
    for xmlpath in args.xmlalignments.split(','):
        xmlaligns.update(copy.deepcopy(readAlignXML(xmlpath).content))

    orths2class = []
    orths2phones = []  # use dictionary for caching
    labels_of_si = []
    siPhones = []

    # now get the class labels using lexiconahndler: input every entry from actualOrth and state number
    lexParsers = []
    lexicons = []
    assert (args.lexiconfile)
    for index,lex in enumerate(args.lexiconfile.split(',')):
        lexParsers.append(make_parser())
        lexicons.append(LexiconHandler(int(args.states.split(',')[index])))
        lexParsers[index].setContentHandler(lexicons[index])
        lexParsers[index].parse(lex)
        orths2phones.append({})
        orths2class.append({})
    	siPhones.append(lexicons[index].getLemmaByOrth("[SILENCE]").phon[0])
        labels_of_si.append(str(lexicons[index].getMixturesByPhon(siPhones[index])[0]))

    numStreams = len(lexicons)
    allpronsCache = []
    prefix = []
    postfix = []
    for i in range(0,numStreams):
        allpronsCache.append({})
        if i < args.scrambleStream:
            prefix.append("0")
        if i > args.scrambleStream:
            postfix.append("0")

    outFile = open(args.output, "wb")
    if args.verbose:
        print "number of files to processed: ", len(xmlaligns)
    else:
        progBar = progressbar.progressBar(0, len(xmlaligns), 77)
        FileCounter = 0
        progBar.draw()

    for rec in xmlaligns:
        lexMixLists = []
        if args.verbose:
            print "current processed segment is " + rec
        else:
            FileCounter += 1
            progBar.updateAmount(FileCounter)
            progBar.draw()

        index = args.scrambleStream
        for align in xmlaligns[rec]:
            orth = align[0].split("/")[0].split(" ")[0]
            if orth not in allpronsCache[index]:
                lemma = lexicons[index].getLemmaByOrth(orth)
                allpronsCache[index][orth] = []
                for pronunciation in lemma.phon:
                    allpronsCache[index][orth].extend(pronunciation)
                allpronsCache[index][orth] = list(set(allpronsCache[index][orth]))
                if len(allpronsCache[index][orth]) > 1:
                    allpronsCache[index][orth].pop(allpronsCache[index][orth].index(u'si'))

            #print "start", align[1], "end", align[2], "orth", orth
            pron_cnt = 0
            state=0
            for frame in range(align[1],align[2]+1):
                if pron_cnt >= len(allpronsCache[index][orth]):
				    pron_cnt=0
				    state=0
                #print pron_cnt, prefix, postfix
                #print len(allpronsCache[index][orth])
                phon = allpronsCache[index][orth][pron_cnt]
                mixtures = lexicons[index].getMixturesByPhon( phon )[state]
                lexMixLists.append( copy.deepcopy(prefix) ) 
                lexMixLists[-1].append(str( mixtures ))
                lexMixLists[-1].extend(postfix)
                #lexMixLists[-1].extend([orth])


                #print frame, "added", mixtures
                pron_cnt += 1

            encodedlist=', '.join(map(unicode, allpronsCache[index][orth]))
            #print allpronsCache[index][orth]
            #print(u'[{}]'.format(encodedlist).encode('UTF-8'))
            #print rec

        if args.useOne:
            newPath = args.images + corpus_name + "/" + rec + "/1"
        else:
            newPath = args.images + corpus_name + "/" + rec 
        #print newPath
        os.chdir(newPath)
        imageList = glob.glob(args.imageExtension)
        # sort the file List according to its names
        imageList.sort()
        imageListLen = len(imageList)
        #print imageListLen

        #print "xxxxxxxxxxx"
        #sys.exit(0)

        if args.outputC3Dstyle:
            # changed this output style, so we have the same number of outputs as inputs
            c3dStartFrame=1
            for imageIndex in xrange(imageListLen):
                if imageIndex >= args.C3DclipLength / 2 and imageIndex < len(lexMixLists) - args.C3DclipLength / 2:
                    c3dStartFrame += 1
                if imageIndex < imageListLen and imageIndex < len(lexMixLists):
                    outFile.write( newPath + '/' + str(imageList[imageIndex]) + ' ' + str(c3dStartFrame) + ' ' + ','.join(lexMixLists[imageIndex]) + '\n')
        else:
            if imageListLen <= len(lexMixLists):
                outFile.write(''.join(  newPath + '/' + str(imageList[imageIndex]) + " " + ','.join(lexMixLists[imageIndex]) + '\n' for imageIndex in xrange(imageListLen)))
            else:
                outFile.write(''.join(  newPath + '/' + str(imageList[imageIndex]) + " " + ','.join(lexMixLists[imageIndex]) + '\n' for imageIndex in xrange(len(lexMixLists))))
	#outFile.close()
		#sys.exit(0)
            #outFile.write(''.join( str(newPath) + image + classes + '\n' for (image, classes) in zip(imageList,outputClasses) ))

class xmlALignmentHandler(xml.sax.ContentHandler):
    search = ""
    found = 0
    buf = ""
    currFrameStart = 0
    currFrameEnd = 0
    currLemma = ""
    currScore = ""
    content = {}
    currRecording = ""
    cnt = []

    def __init__(self):
        self.cnt = []
        del self.cnt[:]
        self.currFrameStart = 0
        self.currFrameEnd = 0
        self.currLemma = ""
        self.currScore = ""
        self.content = {}
        self.content.clear()
        self.currRecording = ""
        pass

    def startDocument(self):
        pass

    def endDocument(self):
        pass

    # def startNode(self, node):
        # print node.nodeValue
        # pass

    def startElement(self, name, attrs):
        if (name == "recording"):
            self.currRecording = attrs.get('name', "")

        if (name == "features"):
            self.currFrameStart = int(attrs.get('start', ""))
            self.currFrameEnd = int(attrs.get('end', ""))
            if self.currRecording not in self.content:
                self.content.setdefault(self.currRecording,[])
                del self.content[self.currRecording][:]
 #           if self.currRecording == '02October_2012_Tuesday_heute_default-5':
 #               print self.currLemma, self.currFrameStart,self.currFrameEnd
            self.content[self.currRecording].append([self.currLemma,self.currFrameStart,self.currFrameEnd])
        if (name == "score"):
            self.buf = []
        if (name == "lemma-pronunciation"):
            self.buf = []

    def endElement(self, name):
        if (name == "lemma-pronunciation"):
            self.currLemma = ""
            if args.subunits is not None:
                self.currLemma = self.buf.strip(" ")
            else:
                self.currLemma = self.buf.strip(" ").split(" ")[0]
            self.buf = []
        if (name == "score"):
            self.currScore = self.buf #[0]
            self.buf = ""
        pass

    def print_frames(self):
        for i in self.frames:
            print ""
            for key in i:
                print key, i[key],

    def characters(self, data):
        pass
        self.buf = data

def readAlignXML(path):
    XMLresultparser = make_parser()
    res = xmlALignmentHandler()
    XMLresultparser.setContentHandler(res)
    infile = gzip.open(path)
    content = infile.read()
    infile.close()
    XMLresultparser.feed(content)
    XMLresultparser.close()
    return res


def generateClassLabel(args):

    # need to encode utf8
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # Read the alignement Cache
    alignmentCaches = args.alignmentcache.split(',')
    acs = []
    for ac in alignmentCaches:
        if args.verbose:
            print ac
        acs.append(open_file_archive(ac))

    # Read the allophone file: allophone information will be matched
    # to the align cache file
    
    if args.allophonefile:
        for index,al in enumerate(args.allophonefile.split(',')):
            acs[index].setAllophones(al)


    # for each (image-allophone-state)  get its corresponding index from the lexicon
    # this will then be used as class labels for caffe
    lexicons = []
    parsers = []
    states = []
    states = map(int,args.states.split(','))
    for index,lex in enumerate(args.lexiconfile.split(',')):
        parsers.append(make_parser())
        lexicons.append(LexiconHandler(states[index]))
        parsers[-1].setContentHandler(lexicons[-1])
        parsers[-1].parse(lex)


    # to match every image with the mix from lexicon file:
    # read the path of the data from alignment cache and store it in the list "dataList"
    # but filter out the paths, which ends with a .attribs
    dataPathList = []

#    print acs[0].file_list()
#    exit()
    for key in acs[0].file_list(): #acs[0].ft:  # keys should be same in all caches,
        #therefore just going for the first alignment cache
        if(".attribs" not in key):
            dataPathList.append(key)


    # for each image get only its state values and allophone of each data and store it in "mixList" 

    if args.verbose:
        print "number of files to processed: ", len(dataPathList)
    else: 
        progBar = progressbar.progressBar(0, len(dataPathList), 77)
        FileCounter = 0
        progBar.draw()

    
    outFile = open(args.output, "wb")
    
    for i in xrange(len(dataPathList)):
        if args.verbose:
            print "current processed segment is " + str(i) + " th data", dataPathList[i]
        else:
            FileCounter += 1
            progBar.updateAmount(FileCounter)   
            progBar.draw()
        #print "the name of the processed data is: " +
        #dataPathList[i]+ "\n"
        mixLists = []
        lexMixLists = []
        for index in xrange(len(acs)):
            acread = acs[index].read(dataPathList[i], "align")
            if args.verbose:
                for align in acread:
                    #print align
                    #print index
                    print acs[index].showAllophone(align[1]) , " --> ", align
                    #print acs[index].allophones[align[1]], " --> ", align
            mixLists.append([(acs[index].showAllophone(align[1]).split('{')[0], align[2]) for align in acread])

        # store the mixtureIndex from the lexicon using allophone name and state and store it in lexMixList
        for imageListIndex in xrange(len(mixLists[0])):
            lexMixLists.append([ str(lexicons[innerindex].getMixturesByPhon(mixLists[innerindex][imageListIndex][0])[mixLists[innerindex][imageListIndex][1]])
                                 for innerindex in xrange(len(acs)) ])
        newPath = "".join([args.images, dataPathList[i]])
    
        # rename Path(when 1 should not be used erase it from the path), check if args.useOne is set: this is for the case, when in some cases the file-directory  structure contains a 1,
        #  for further questions, ask Oscar Koller, Sepehr Zargaran, Ji-seung Shin     
        if not args.useOne:
            newPath = newPath[:-2]      
        if args.outputC3Dstyle:  
            os.chdir(newPath)
            imageListLen = len(glob.glob(args.imageExtension))
            imageList = [''] * imageListLen
        else:
            os.chdir(newPath)
            imageList = glob.glob(args.imageExtension)
            # sort the file List according to its names
            imageList.sort()
            imageListLen = len(imageList)
        # write out
        if len(imageList) != len(lexMixLists):
            #for im in xrange(len(imageList)):
            #    print im, imageList[im]
            #print ""
            #for im in xrange(len(lexMixLists)):
            #    print im, lexMixLists[im]
            if not args.ignoreDifferentLengths:
                print 'error:', dataPathList[i], 'number of images ' + str(len(imageList)) + ' != ' + str(len(lexMixLists)) + ' alignment count '
		exit()
            else:
                print 'warning:', dataPathList[i], 'number of images ' + str(len(imageList)) + ' != ' + str(len(lexMixLists)) + ' alignment count '
                
        if args.outputC3Dstyle:
            # changed this output style, so we have the same number of outputs as inputs
            c3dStartFrame=1
            for imageIndex in xrange(imageListLen):
                if imageIndex >= args.C3DclipLength / 2 and imageIndex < len(lexMixLists) - args.C3DclipLength / 2:
                    c3dStartFrame += 1
                if imageIndex < imageListLen and imageIndex < len(lexMixLists):
                    outFile.write( newPath + '/' + str(imageList[imageIndex]) + ' ' + str(c3dStartFrame) + ' ' + ','.join(lexMixLists[imageIndex]) + '\n')
        else:
            if imageListLen <= len(lexMixLists):
                outFile.write(''.join(  newPath + '/' + str(imageList[imageIndex]) + " " + ','.join(lexMixLists[imageIndex]) + '\n' for imageIndex in xrange(imageListLen)))
            else:
                outFile.write(''.join(  newPath + '/' + str(imageList[imageIndex]) + " " + ','.join(lexMixLists[imageIndex]) + '\n' for imageIndex in xrange(len(lexMixLists))))
    outFile.close()


#########################################################################################################################################

class Convert_Orth:

	def __init__(self, number_of_streams, lexicons, si_phones):
		self.lexicons = lexicons
		self.number_of_streams = number_of_streams
		self.si_phones = si_phones
		self.phones = []
		self.class_ids = []
		for i in range(0,number_of_streams):
			self.phones.append({})
			self.class_ids.append({})
	
	def get_phones(self, stream_id, orth):
		if orth not in self.phones[stream_id]:
			lemma = self.lexicons[stream_id].getLemmaByOrth(orth)
			if lemma == None:
				phones = [ self.si_phones[stream_id] ]
			else:
				phones = self.lexicons[stream_id].getLemmaByOrth(orth).phon
			#b = len(phones) -1
			#phones[0],phones[b] = phones[b],phones[0]
			if args.removeSilenceFromPronunciations:
				#print "GET_PHoNES: REMOVESIL b", phones
				for phonseq in phones:
					while self.si_phones[stream_id][0] in phonseq and len(phonseq) > 1:
						#print "removing"
						phonseq.pop(phonseq.index(self.si_phones[stream_id][0]))
				#print "GET_PHoNES: REMOVESIL a" , phones
			self.phones[stream_id][orth] = []
			for phonseq in phones:
				is_silence_pronunciation = False
				if self.si_phones[stream_id] == phonseq and args.removeSilenceFromPronunciations and len(phones) > 1:
					is_silence_pronunciation = True
				if phonseq not in self.phones[stream_id][orth] and is_silence_pronunciation is False:
					self.phones[stream_id][orth].append(phonseq)
			if args.verbose:
				print "    phones[",stream_id, "]", self.phones[stream_id], "lemma", self.lexicons[stream_id].getLemmaByOrth(orth)

		return self.phones[stream_id][orth]

	def get_class_ids(self, stream_id, orth):
		if orth not in self.class_ids[stream_id]:
			phones = self.get_phones(stream_id, orth)
			self.class_ids[stream_id][orth] = []
			for phonseq in phones:
				self.class_ids[stream_id][orth].append([])
				for phon in phonseq:
					self.class_ids[stream_id][orth][-1].extend([n for n in self.lexicons[stream_id].getMixturesByPhon(phon)])
		return self.class_ids[stream_id][orth]

class Linear_Aligner:

    def __init__(self):
        self.beginSilence = int(args.beginSilence)
        self.endSilence = int(args.endSilence)
        self.borderSilence = int(args.borderSilence)
        self.midSilence = int(args.midSilence)

    def depth(self,l):
        if isinstance(l, list):
            return 1 + max(self.depth(item) for item in l)
        else:
            return 0

    def change_sil_padding(self, beginSil, endSil, borderSil, midSil):
            self.beginSilence = beginSil
            self.endSilence = endSil
            self.borderSilence = borderSil
            self.midSilence = midSil    

    def get_align(self, sequence_length, state_list, si_label):
            imageListLen = sequence_length
            wordCount = len(state_list)
            beginSil = self.beginSilence
            endSil = self.endSilence
            borderSil = self.borderSilence
            midSil = self.midSilence

            assert self.depth(state_list) == 2 # make sure state_list is structured as follows: [ [word1-phon1 word1-phon2] [ word2-phon1 ] [word3-phon1 word3-phon2 word3-phon3] ] 
            minStateLength = len([phon for word in state_list for phon in word])
            
            expandedStateList = copy.deepcopy(state_list)

            # make sure to reduce silences, if the segment is too short
            if 2 * borderSil + midSil * (wordCount - 1) + beginSil + endSil + minStateLength > imageListLen:
                diff = 2 * borderSil + midSil * (wordCount - 1) + beginSil + endSil + minStateLength - imageListLen
                #we cant use all the silence: sentence is too short: set them all to 0
                if args.verbose:
                    print "WARNING: too few frames to add the requested silence: reducing silence."
                while diff != 0:
                    if beginSil > 0:
                        beginSil -= 1
                    if borderSil > 0:
                        borderSil -= 1
                    if endSil > 0:
                        endSil -= 1
                    if midSil > 0:
                        midSil -= 1
                    diff = 2 * borderSil + midSil * (wordCount - 1) + beginSil + endSil + minStateLength - imageListLen
                    if beginSil == 0 and borderSil == 0 and endSil == 0 and midSil == 0:
                        break

            workingLen = imageListLen - 2 * borderSil - midSil * (wordCount - 1) - beginSil - endSil

            outputClasses = [""] * imageListLen
            image = 0

            # add start silence
            for sils in xrange(borderSil + beginSil):
                if image < imageListLen:
                    outputClasses[image] += si_label
                    image += 1

            # prepare actual word states.
            # go over each state and duplicate it. then go to next state
            # do that until all our frames are taken
            # maintain word boundaries, so we can later add silence in between of them
            stateListWordIndex = 0
            stateListStateIndex = 0
            expandedStateListStateIndex = 0
            expandedStateListWordIndex = 0
            expandedJump = 2

            # first do a full expand, eg. adding to each word the same amount of frames
            runcnt = 1  # the first run is already in the list by copying.
            fullruns = workingLen / minStateLength
            if args.verbose:
                print "\n","Full duplications of every state:", fullruns, "stateCount", minStateLength, "no-sil-frames="+str(workingLen), "all-frames="+str(imageListLen)
            while runcnt < fullruns:
                currState = state_list[stateListWordIndex][stateListStateIndex]
                if args.verbose:
                    print "origStates("+str(len(state_list))+")", state_list
                    print "beforeChanges", expandedStateList
                expandedStateList[expandedStateListWordIndex].insert(expandedStateListStateIndex,currState)
                if args.verbose:
                    print "after Changes", expandedStateList
                expandedStateListStateIndex += expandedJump  # increment by 2 because we have just duplicated the current state
                minStateLength += 1
                stateListStateIndex += 1
                if stateListStateIndex >= len(state_list[stateListWordIndex]):
                    stateListStateIndex = 0
                    expandedStateListStateIndex = 0
                    expandedStateListWordIndex += 1
                    stateListWordIndex += 1
                if stateListWordIndex >= len(state_list):  # we are at the end of the sentence
                    stateListWordIndex = 0
                    expandedStateListWordIndex = 0
                    expandedJump += 1
                    runcnt += 1

            if args.verbose:
                print "Lexicon","Partial duplications of every state following.", fullruns, "stateCount", minStateLength, "available frames (without silence)", workingLen

            # then for the remainder double only the last state in each word
            jumpCount=0
            while minStateLength < workingLen:
                stateListStateIndex = len(state_list[stateListWordIndex]) - 1 - jumpCount
                if stateListStateIndex < 0:
                    stateListStateIndex = len(state_list[stateListWordIndex]) - 1
                expandedStateListStateIndex = len(expandedStateList[expandedStateListWordIndex]) - 1 - jumpCount * expandedJump
                if expandedStateListStateIndex < 0:
                    expandedStateListStateIndex = len(expandedStateList[expandedStateListWordIndex]) - 1
                currState = state_list[stateListWordIndex][stateListStateIndex]
                #print "origStatesLis("+str(len(stateList[i]))+")", stateList[i]
                #print "beforeChanges("+str(sum(np.array(map(len, expandedStateList[i]))))+")", expandedStateList[i]
                expandedStateList[expandedStateListWordIndex].insert(expandedStateListStateIndex,currState)
                #print "after Changes("+str(sum(np.array(map(len, expandedStateList[i]))))+")", expandedStateList[i]
                minStateLength += 1
                stateListWordIndex += 1
                expandedStateListWordIndex += 1
                if stateListWordIndex >= len(state_list):  # we are at the end of the sentence
                    jumpCount += 1
                    stateListWordIndex = 0
                    expandedStateListWordIndex = 0

            # go over each word, and add silence if needed
            for w in xrange(wordCount):
                for c in expandedStateList[w]:
                    if image < imageListLen:
                        outputClasses[image] += str(c)
                        image += 1
                if w != wordCount - 1:  # the last word in segment does not need intermediate silence
                    for sils in xrange(midSil):
                        if image < imageListLen:
                            outputClasses[image] += si_label
                            image += 1

            # add end silence
            for sils in xrange(borderSil + endSil):
                if image < imageListLen:
                    outputClasses[image] += si_label
                    image += 1
            return copy.deepcopy(outputClasses)

def getNumberOfImages(corpus_name, rec_name):
        if args.useOne:
            path = args.images + corpus_name + "/" + rec_name + "/1/"
        else:
            path = args.images + corpus_name + "/" + rec_name + "/"
        if args.ignoreMissingImages and not os.path.exists(path):
			return (None, None, None)
        if args.outputC3Dstyle:
            os.chdir(path)
            return (path, None, len(glob.glob(args.imageExtension)))
        else:
            os.chdir(path)
            imageList = glob.glob(args.imageExtension)
            # sort the file List according to its names
            imageList.sort()  
            return (path, imageList, len(imageList))

def write_to_file(out_file_handle, alignment, image_path, imageList):
        # write segment
        if args.outputC3Dstyle:
            # changed this output style, so we have the same number of outputs as inputs
            c3dStartFrame=1
            for imageIndex in xrange(imageListLen):
                if imageIndex >= args.C3DclipLength / 2 and imageIndex < len(outputClasses) - args.C3DclipLength / 2:
                    c3dStartFrame += 1
                out_file_handle.write(image_path + ' ' + str(c3dStartFrame ) + ','.join(alignment[imageIndex]) + '\n')

#                outFile.write( str(imageList[imageIndex]) + ' ' + str(c3dStartFrame) + ' ' + ','.join(outputClasses[imageIndex]) + '\n')
        else:
            out_file_handle.write(''.join( str(image_path) + image + " " + ','.join(classes) + '\n' for (image, classes) in zip(imageList,alignment) ))


# function to write a image class label according the corpus, states, silentratio
def generateLinearAlignedClassLabel(args):

    # need to encode utf8
    reload(sys)
    sys.setdefaultencoding('utf-8') 

    # read the corpus
    corpusfile = args.corpus
    parser = make_parser()
    corpus = CorpusHandler(encoding="UTF-8",includedir=corpusfile )
    parser.setContentHandler(corpus)
    parser.parse(corpusfile)

    labels_of_si = []
    siPhones = []
    
    # now get the class labels using lexiconahndler: input every entry from actualOrth and state number
    lexParsers = []
    lexicons = []
    for index,lex in enumerate(args.lexiconfile.split(',')):
        lexParsers.append(make_parser())
        lexicons.append(LexiconHandler(int(args.states.split(',')[index])))
        lexParsers[index].setContentHandler(lexicons[index])
        assert (args.lexiconfile)
        lexParsers[index].parse(lex)
        siPhones.append(lexicons[index].getLemmaByOrth("[SILENCE]").phon[0])
        labels_of_si.append(str(lexicons[index].getMixturesByPhon(siPhones[index])[0]))
        
    numStreams = len(lexicons)
    
    convert_orth = Convert_Orth(numStreams, lexicons, siPhones)
    linear_aligner = Linear_Aligner()

    if args.verbose:
        print "number of files to processed: ", len(corpus.recordings)
    else: 
        progBar = progressbar.progressBar(0, len(corpus.recordings), 77)
        FileCounter = 0
        progBar.draw()
        
    if args.maximum_pronunciation_number_to_consider is None:
        maximum_pronunciation_number_to_consider = 999999
    else:
        maximum_pronunciation_number_to_consider = args.maximum_pronunciation_number_to_consider

    outFileHandle = open(args.output, "wb")
    for rec in corpus.recordings:
        if args.verbose:
            print ""
            print "segment", rec.name, "orth", rec.orth
            for i in xrange(numStreams):
                print "lexicon("+str(i)+")", [convert_orth.get_phones(i, o) for o in rec.orth]#,"   stateList("+str(i)+")", stateList[i]
        (image_path, imageList, imageListLen) =  getNumberOfImages(corpus.name, rec.name)
        if args.ignoreMissingImages and imageListLen is None:
            continue
        elif imageListLen is None:
            print "error, directory", rec.name,"does not exist"
            sys.exit()
        final_alignments = []
        for i in xrange(numStreams):
            num_words = len(rec.orth)
            pron_index = [0] * num_words
            all_prons_done = False
            prons_done = [False] * num_words
            alignments = []
            while not all_prons_done:
                expandedStateList = []

                for word_index, currentOrth in enumerate(rec.orth):
                    expandedStateList.append(copy.deepcopy([word for word in convert_orth.get_class_ids(i, currentOrth)][pron_index[word_index]]))

                all_prons_done = True
                for word_index, currentOrth in enumerate(rec.orth):
                    pron_index[word_index] += 1
                    if pron_index[word_index] < len(convert_orth.get_class_ids(i, currentOrth)) and pron_index[word_index] < maximum_pronunciation_number_to_consider:
                        if prons_done[word_index] is False:
                            all_prons_done = False
                    else:
                        prons_done[word_index] = True
                        pron_index[word_index] = 0

                #print expandedStateList
                alignments.append(copy.deepcopy(linear_aligner.get_align(imageListLen, expandedStateList, labels_of_si[i])))

            #scramble all possible alignments
            num_alignments = len(alignments)
            align_index = 0
            for n in xrange(imageListLen):
                if n >= len(final_alignments):
                    final_alignments.append([])
                final_alignments[n].append(alignments[align_index][n])
                align_index += 1
                if align_index >= num_alignments:
                    align_index = 0
        write_to_file(outFileHandle, final_alignments, image_path, imageList)
        if not args.verbose:
            FileCounter += 1
            progBar.updateAmount(FileCounter)
            progBar.draw()

        #print final_alignments
           
    outFileHandle.close()

###########################################################################################

def generateScrambledLinearAlignmentV2(args):
    # need to encode utf8
    reload(sys)
    sys.setdefaultencoding('utf-8')
    print args.verbose
    # read the corpus
    corpusfile = args.corpus
    parser = make_parser()
    corpus = CorpusHandler(encoding="UTF-8",includedir=corpusfile )
    parser.setContentHandler(corpus)
    parser.parse(corpusfile)

    corpus_name = corpus.name

    xmlaligns={}
    for xmlpath in args.xmlalignments.split(','):
        xmlaligns.update(copy.deepcopy(readAlignXML(xmlpath).content))

    orths2class = []
    orths2phones = []  # use dictionary for caching
    labels_of_si = []
    siPhones = []

   # now get the class labels using lexiconahndler: input every entry from actualOrth and state number
    lexParsers = []
    lexicons = []
    for index,lex in enumerate(args.lexiconfile.split(',')):
        lexParsers.append(make_parser())
        lexicons.append(LexiconHandler(int(args.states.split(',')[index])))
        lexParsers[index].setContentHandler(lexicons[index])
        assert (args.lexiconfile)
        lexParsers[index].parse(lex)
        siPhones.append(lexicons[index].getLemmaByOrth("[SILENCE]").phon[0])
        labels_of_si.append(str(lexicons[index].getMixturesByPhon(siPhones[index])[0]))

    numStreams = len(lexicons)

    convert_orth = Convert_Orth(numStreams, lexicons, siPhones)
    linear_aligner = Linear_Aligner() 

    if args.verbose:
        print "number of files to processed: ", len(corpus.recordings)
    else:
        progBar = progressbar.progressBar(0, len(corpus.recordings), 77)
        FileCounter = 0
        progBar.draw()

    if args.maximum_pronunciation_number_to_consider is None:
        maximum_pronunciation_number_to_consider = 999999
    else:
        maximum_pronunciation_number_to_consider = args.maximum_pronunciation_number_to_consider

    outFileHandle = open(args.output, "wb")

    if args.verbose:
        print "number of files to processed: ", len(xmlaligns)
    else:
        progBar = progressbar.progressBar(0, len(xmlaligns), 77)
        FileCounter = 0
        progBar.draw()

    for rec in xmlaligns:
        (image_path, imageList, imageListLen) =  getNumberOfImages(corpus_name, rec)
        
        if args.verbose:
            print "current processed segment is " + rec
        else:
            FileCounter += 1
            progBar.updateAmount(FileCounter)
            progBar.draw()

        index = args.scrambleStream
        num_words = len(xmlaligns[rec])
        for align in xmlaligns[rec]:
            orth = align[0].split("/")[0].split(" ")[0]
            #print align
    
            if args.verbose is True:
                print ""
                print "segment", rec, "orth", orth
                for i in xrange(numStreams):
                    print "lexicon("+str(i)+")", convert_orth.get_phones(i,orth) #,"   stateList("+str(i)+")", stateList[i]

            #(image_path, imageList, imageListLen) =  getNumberOfImages(corpus.name, rec.name)
            #if args.ignoreMissingImages and imageListLen is None:
            #    continue
            #elif imageListLen is None:
            #    print "error, directory", rec.name,"does not exist"
            #    sys.exit()
        final_alignments = []
        for i in xrange(numStreams):
            #num_words = len(rec.orth)
            pron_index = [0] * num_words
            all_prons_done = False
            prons_done = [False] * num_words
            alignments = []
            linear_aligner.change_sil_padding(0,0,0,0)

            while not all_prons_done:
                expandedStateList = []
   
                alignments.append([]) 
                for word_index, align in enumerate(xmlaligns[rec]):
                    expandedStateList = []
                    currentOrth = align[0].split("/")[0].split(" ")[0]
                    alignmentLen = align[2]+1 - align[1]

                    expandedStateList.append(copy.deepcopy([word for word in convert_orth.get_class_ids(i, currentOrth)][pron_index[word_index]]))
                    alignments[-1].extend(copy.deepcopy(linear_aligner.get_align(alignmentLen, expandedStateList, labels_of_si[i])))

                #    print "tmp",word_index," stream",i, currentOrth ,expandedStateList, "aligned", alignments[-1]
                #print "stream",i,expandedStateList
                all_prons_done = True

                for word_index, align in enumerate(xmlaligns[rec]):
                    currentOrth = align[0].split("/")[0].split(" ")[0]
                    pron_index[word_index] += 1
                    if pron_index[word_index] < len(convert_orth.get_class_ids(i, currentOrth)) and pron_index[word_index] < maximum_pronunciation_number_to_consider:
                        if prons_done[word_index] is False:
                            all_prons_done = False
                    else:
                        prons_done[word_index] = True
                        pron_index[word_index] = 0
    
                #print expandedStateList
                    alignmentLen = align[2]+1 - align[1]
                    linear_aligner.change_sil_padding(0,0,0,0)
                    alignments[-1].extend(copy.deepcopy(linear_aligner.get_align(alignmentLen, expandedStateList, labels_of_si[i])))
                alignments[-1].extend(labels_of_si[i])  
            #scramble all possible alignments
            num_alignments = len(alignments)
            align_index = 0
            for n in xrange(imageListLen):
                if n >= len(final_alignments):
                    final_alignments.append([])
                final_alignments[n].append(alignments[align_index][n])
                align_index += 1
                if align_index >= num_alignments:
                    align_index = 0
        write_to_file(outFileHandle, final_alignments, image_path, imageList)
        if not args.verbose:
            FileCounter += 1
            progBar.updateAmount(FileCounter)
            progBar.draw()
        #sys.exit()
    
    







if __name__ == "__main__":
    #t1 = time.clock()
    main()
    #t2 = time.clock()
    #print round(t2-t1, 3)
