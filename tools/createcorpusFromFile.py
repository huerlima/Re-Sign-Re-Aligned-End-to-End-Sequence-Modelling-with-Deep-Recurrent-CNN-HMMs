#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
create corpus from file.

This is inspired by CSV file structure.  First row should contain
field names that can occur in a bliss corpus file, following rows the
corresponding data information, e.g.
  name;video;orth;phonemes
  ae07_001;ae07_001.png;arabicword;aaA laB shM raE aaA yaB ayE

"""

__version__ = "$Revision: 1.7 $"

import sys
from optparse import OptionParser
from handlers import CorpusHandler
from corpus import Corpus
from corpuselements import Recording
from speaker import Speaker
from string import join
from xml.sax import make_parser
from utilities import *
from sets import Set
from miscLib import uopen, uclose

def saveRecordings(corpus, speakers, recordings, filename, encoding):
    # @todo: handle speaker names
    newCorpus = Corpus(corpus.name, encoding=encoding)
    for s in corpus.speakers:
        if s in speakers or speakers == []:
            gender="male" #default
            for description in corpus.descriptions:
                if description.name == s:
                    gender=description.gender
                    break
            newCorpus.addSpeakerDescription(s, gender)
    for rec in recordings:
        newCorpus.addRecord(rec, False)
    newCorpus.save(filename)


def countWords(recordings):
    words = []
    wordcount = {}
    for rec in recordings:
        for word in rec.orth:
            if not word in words:
                words.append(word)
                wordcount[word] = 1
            else:
                wordcount[word] += 1
    return wordcount


def main(argv):
    defaultEncoding     = "utf8"
    
    usage="usage: %prog [options] <corpus name> <corpus outfile>\n " + __doc__
    optionParser = OptionParser(usage = usage)
    optionParser.add_option("-E", "--encoding", default=defaultEncoding, dest="encoding",
                            help="encoding ["+defaultEncoding+"]")
    optionParser.add_option("-f", "--file", dest="sourcefilename",
                            help="source filename with at least sentence IDs and orthographies specified in a file");
    optionParser.add_option("-F", "--Field", default="orth", dest="orthfieldname",
                            help="orth field name, e.g. orth or zip [orth]")
    optionParser.add_option("-d", "--delimiter", default=";", dest="delimiter",
                            help="field delimiter in the plain file [;]")
    optionParser.add_option("-a", "--all", dest="splitall", action="store_true",
                            help="split every record into a single corpus file")
    optionParser.add_option("-w", "--wordcount", dest="wordlist", action="store_true",
                            help="print word list")
    optionParser.add_option("-v", "--verbose", dest="verbose", action="store_true")
    (options, args) = optionParser.parse_args()

    if len(args) != 2 :
        optionParser.error("incorrect number of arguments %d" % len(args))
        sys.exit()

    #set filenames
    corpusname=args[0]
    corpusFilename=args[1]
    
    if not corpusFilename.rfind(".corpus"):
        corpusFilename+=".corpus"
    recordingsFilename=corpusFilename[:corpusFilename.rfind('.')]+".recordings"
    speakerDescriptionFilename =  corpusFilename[:corpusFilename.rfind('.')]+".speaker"

    if options.verbose:
        print "corpusFilename =", corpusFilename
        print "speakerDescriptionFilename =", speakerDescriptionFilename
        print "recordingsFilename =", recordingsFilename

    #create corpus include structure
    newCorpus          = Corpus(corpusname, encoding="utf8")
    newCorpus.includeFile(os.path.abspath(speakerDescriptionFilename))
    newCorpus.includeFile(os.path.abspath(recordingsFilename))
    newCorpus.save(corpusFilename)

    # create default speaker description file
    speakers=[]
    speakerDescription = Speaker(corpusname, encoding="utf8")
   
    #read sentence IDs and structure information
    sentenceIDsFile = uopen(options.sourcefilename,options.encoding,'r')
   # sentenceIDsFile = open(options.sourcefilename,'r')
    firstLine = sentenceIDsFile.readline()[:-1]
 #   fieldList = unicode(firstLine, options.encoding).split(options.delimiter)
    fieldList = firstLine.split(options.delimiter)
    if options.verbose:
        print "structure:", firstLine, fieldList
    fieldMap={}
    fieldId=0
    for field in fieldList:
        fieldMap[field]=fieldId
        if options.verbose :
            print field, fieldId
        fieldId+=1

    #check required fields
    if not fieldMap.has_key('name') or not fieldMap.has_key('video') or not fieldMap.has_key('orth'):
        print "ERROR: one or more required fields [name,video, and/or orth] are missing."
        keys = fieldMap.keys()
        keys.sort
        for key in keys:
            print key, fieldMap[key]
        sys.exit()

    #create recordings from data info file
    newRecordings = Corpus(corpusname, encoding="utf-8")
    sentenceCnt=0
    for line in sentenceIDsFile:
        sentenceCnt += 1
 #       splitlist = unicode(line, options.encoding).strip().split(options.delimiter)
	splitlist = line.strip().split(options.delimiter)
        if options.verbose:
            for i in range(0,len(splitlist)):
                print i, splitlist[i]
        if len(splitlist) < len(fieldMap):
	    if options.verbose:
                print "ERROR: data row '%s' is invalid and will be discarded." % (splitlist)
        else:            
            start=-1
            end=-1
            speakerName="default"
            speakerGender="male"
            recordOrth=""
            recordTranslation=""
            
            if(fieldMap.get("start") != None) :
                start=splitlist[fieldMap['start']]
            if(fieldMap.get("end") != None) :
                end=splitlist[fieldMap['end']]
            if(fieldMap.get("speaker") != None) :
                speakerName=splitlist[fieldMap['speaker']]
            if(fieldMap.get("gender") != None) :
                speakerGender=splitlist[fieldMap['gender']]
            if(fieldMap.get("translation") != None) :
                recordTranslation=splitlist[fieldMap['translation']]

            # update speaker names
            if speakerName not in speakers:
                speakerDescription.addSpeakerDescription(speakerName, speakerGender);
                speakers.append(speakerName);
                
            # add recording
            newRecordings.addRecording(splitlist[fieldMap['name']], splitlist[fieldMap['video']],
                                       start, end, speakerName,
                                       splitlist[fieldMap[options.orthfieldname]], False, recordTranslation)

    # close corpus and write to xml file
    uclose(sentenceIDsFile)
    newRecordings.save(recordingsFilename)
    speakerDescription.save(speakerDescriptionFilename)
    
    print "\n----------------------------------------------------------"
    print "corpus file               :'" + corpusFilename + "'"
    print "speaker description file  :'" + speakerDescriptionFilename + "'"
    print "recordings file           :'" + recordingsFilename + "'"
    print



if __name__ == "__main__":
    main(sys.argv)
