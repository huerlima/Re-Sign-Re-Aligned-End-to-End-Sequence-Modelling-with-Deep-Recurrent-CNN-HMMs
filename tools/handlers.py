#!/usr/bin/env python
#-*- coding: utf-8 -*-
#$Id: handlers.py,v 1.25 2006-10-12 19:12:41 dreuw Exp $

from xml.sax import \
     ContentHandler, \
     make_parser
import sys, pickle, re
from string import \
     atof, \
     join
from patterns import *
from corpuselements import *


################################################################################################################
class BostonXML2txt(ContentHandler):

    def __init__(self):
        self.data            = []
        self.participants    = []
        self.fields          = []
        self.mediabasepath   = ""
        self.videosuffix     = ".avi"
        self.mediaFiles      = []
        self.utterances      = []
        self.glossName       = ""
        self.glossId         = -1
        self.translationName = ""
        self.translationId   = -1
        self.trackOpen       = 0
        
    def startDocument(self):
        pass
    
    def startElement(self, name, attrs):
        if name == "FIELD":
            self.setField(int(attrs.get('ID')), attrs.get('NAME'))
        elif name == "MEDIA-FILE":
            self.setMediaFile(int(attrs.get('ID')), attrs.get('LEGACY-PATH'))
        elif name == "UTTERANCE":
            self.setUtterance(int(attrs.get('ID')), attrs.get('EXCERPT'), int(attrs.get('S')), int(attrs.get('E')))
        elif name == "NOTES": #this might be wrong if participant or other notes are given
            self.data = []
        elif name == "MEDIA-REF":
            self.setUtteranceMediaRef(int(attrs.get('ID')))
        elif name == "SEGMENT":
            self.setUtteranceSegmment(int(attrs.get('PARTICIPANT-ID')))
        elif name == "TRACK":
            if (int(attrs.get('FID')) == self.glossId):
                self.setUtteranceSegmentTrack(int(attrs.get('FID')))
            elif (int(attrs.get('FID')) == self.translationId):
                self.setUtteranceSegmentTrack(int(attrs.get('FID')))
            #else:
            #    print "wrong id =", int(attrs.get('FID'))
        elif name == "A" and self.trackOpen:
            self.data = []
            vid=-1
            if attrs.get('VID'):
                vid=int(attrs.get('VID'))
            self.setUtteranceSegmentTrackAnnotation(int(attrs.get('S')), int(attrs.get('E')), vid)
        elif name == "PARTICIPANT":
            self.setParticipant(int(attrs.get('ID')), attrs.get('NAME'), attrs.get('LABEL'), int(attrs.get('AGE')), attrs.get('GENDER'), attrs.get('LANGUAGE'))                            
    def characters(self, cdata):
        self.data.append(cdata)    

    def endElement(self, name):
        if name == "TRACK" and self.trackOpen:
            self.trackOpen = 0
        elif name == "NOTES":
            self.setUtteranceNotes(join(self.data).strip())
        elif name == "A" and self.trackOpen:
            anno = join(self.data).strip()
            vid  = self.utterances[-1].segments[-1].tracks[-1].annotations[-1].vid
            # dirty: these values should be also extracted from the xml files
            if(vid==400000):
                anno="[HOLD]"
            elif(vid==400001):
                anno="[ONSET]"
            elif(vid==400002):
                anno="[OFFSET]"                
            self.utterances[-1].segments[-1].tracks[-1].annotations[-1].value=anno
 
    def endDocument(self):
        pass

    def setField(self, id, name):
        if (name == self.glossName):
            self.glossId=id
        elif (name == self.translationName):
            self.translationId=id
        self.fields.append(FieldAnnotation(id, name))

    def setMediaFile(self, id, path):
        path_parts = path.split(':')
        basename   = path_parts[-1][:-4] + self.videosuffix
        cameratype = path_parts[-2][:6]
        if not cameratype in ["master", "slave1", "slave2", "slave3"]:
            cameratype="unknown"
        ##path example: 'NCSLGRv2:video files:master:b-881_698_master_small.mov'
##        if self.videosuffix == ".avi":
##            basename = basename.replace("master_small", "small_0")
##            basename = basename.replace("slave1_small", "small_1")
##            basename = basename.replace("slave2_small", "small_2")
##            basename = basename.replace("slave3_small", "small_3")
##            basename = basename.replace("0_0", "0")
        self.mediaFiles.append(MediaFileAnnotation(id, self.mediabasepath + basename, cameratype))


    def setUtterance(self, id, excerpt, start, end):
        self.utterances.append(Utterance(id, excerpt, start, end))

    def setUtteranceMediaRef(self, id):
        self.utterances[-1].medias.append(id)

    def setUtteranceSegmment(self, id):
        self.utterances[-1].segments.append(Segment(id))

    def setUtteranceSegmentTrack(self, id):
        self.utterances[-1].segments[-1].tracks.append(Track(id))
        self.trackOpen = 1

    def setUtteranceSegmentTrackAnnotation(self, start, end, vid):
        self.utterances[-1].segments[-1].tracks[-1].annotations.append(Annotation(start, end, vid))

    def setUtteranceNotes(self, notes):
        try:
            self.utterances[-1].notes = notes
        except IndexError:
            pass

    def setParticipant(self, id, name, label, age, gender, language):
        self.participants.append(Participant(id, name, label, age, gender, language))

    def getFieldId(self, fieldName):
        for field in self.fields:
            if field.name == fieldName:
                return field.id
        raise KeyError(fieldName)

    def getFieldName(self, fieldId):
        for field in self.fields:
            if field.id == fieldId:
                return field.id
        raise KeyError(fieldId)

    def getMediaFileId(self, mediaPath):
        for mediaFile in self.mediaFiles:
            if mediaFile.path == mediaPath:
                return mediaFile.id
        raise KeyError(mediaPath)

    def getMediaFilePath(self, mediaFileId):
        for mediaFile in self.mediaFiles:
            if mediaFile.id == mediaFileId:
                return mediaFile.path
        raise KeyError(mediaFileId)

    def getMedia(self, mediaFileId):
        for mediaFile in self.mediaFiles:
            if mediaFile.id == mediaFileId:
                return mediaFile
        raise KeyError(mediaFileId)

    def getParticipant(self, id):
        for participant in self.participants:
            if participant.id == id:
                return participant
        raise KeyError(id)


################################################################################################################
class CorpusHandler(ContentHandler) :

    def __init__(self, encoding="utf8", includedir="."):
        self.wordcount = {}
        self.wordlen = {}
        self.orth  = 0
        self.translation = 0
        self.gender  = 0
        self.curword = ""
        self.curlen = 0
        self.recordings = []
        self.speakers = []
        self.descriptions = []
        self.name = ""
        self.encoding=encoding
        self.verbose=True
        self.includedir=includedir
             
    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        if name == "corpus":
            self.name = attrs.get('name')
        if name == "recording":
            self.cur_record = Recording()
            self.cur_record.name = attrs.get('name')
            self.cur_record.video = attrs.get('video')
        elif name == "segment":
            if attrs.get('start'):
                self.cur_record.start = atof(attrs.get('start'))
            if attrs.get('end'):
                self.cur_record.end = atof(attrs.get('end'))
            if attrs.get('start') and attrs.get('end'):
                self.curlen = atof(attrs.get('end')) - atof(attrs.get('start'))
        elif name == "speaker":
            self.cur_record.speaker = attrs.get('name')
            if not self.cur_record.speaker in self.speakers:
                self.speakers.append(self.cur_record.speaker)
        elif name == "speaker-description":
            self.cur_speaker_description = Speaker()
            self.cur_speaker_description.name = attrs.get('name')
        elif name == "gender":
            self.gender = 1
            self.charbuf = ""
        elif name == "orth":
            self.orth = 1
            self.charbuf = ""
        elif name == "translation":
            self.translation = 1
            self.charbuf = ""
        elif name == "include":
            parser = make_parser()
            parser.setContentHandler(self)
            file=attrs.get('file')            
            if (file[0] == "/" or file[0] == "."):
                parser.parse(file)
            else:
                parser.parse(self.includedir+"/"+file)
		
    def characters(self, char):
        if self.orth or self.translation or self.gender:
            self.charbuf += char

    def endElement(self,name):
        if name == "orth":
            #print "REPR", `self.charbuf`
            self.curword=self.charbuf.strip() 
            ## sentence work-around for word lengths
            singleWords=self.curword.split(' ')
            self.cur_record.orth = singleWords
            wordLength = self.curlen;
            if len(singleWords) != 1:
                #wordLength /= len(singleWords)  ##average length would be added
                wordLength = 0                   ##ignore sentences for word lengths
                
            for sWord in singleWords:
                if sWord != "[SILENCE]" and sWord != "[UNKNOWN]":
                    try:
                        self.wordcount[sWord] += 1
                        self.wordlen[sWord]   += wordLength ## sentence work-around
                    except KeyError:
                        self.wordcount[sWord] = 1
                        self.wordlen[sWord]   = wordLength ## sentence work-around
                        baseWord=parseAndDeleteCenterPattern(sWord, pattern_plus)
                        if baseWord != sWord:
                            ## implicitely init at least one GLOSS++->GLOSS
                            self.wordlen[baseWord] = 0
                            self.wordcount[baseWord] = 0                        
                        
            self.orth = 0
        elif name == "translation":
            self.cur_record.translation = self.charbuf.strip()
            self.translation = 0
        elif name == "recording":
            self.recordings.append(self.cur_record)
        elif name == "gender":
            self.cur_speaker_description.gender = self.charbuf.strip()
            self.gender = 0
        elif name == "speaker-description":
            self.descriptions.append(self.cur_speaker_description)


    def endDocument(self):
        for word in self.wordcount:
            try:
                self.wordlen[word] = self.wordlen[word] / self.wordcount[word]
            except ZeroDivisionError:
                # this can happen if you observed only GLOSS++ but never a single GLOSS
                pass

        # calculate scores
        for currentRecord in range(0,len(self.recordings)):
            for word in self.recordings[currentRecord].orth:
                if word != "[SILENCE]" and word != "[UNKNOWN]":
                    self.recordings[currentRecord].score += self.wordcount[word]-1 #don't know why '-1' ?! but it's right ...
            self.recordings[currentRecord].score /= len(self.recordings[currentRecord].orth)
                
    def getWords(self):
        return self.wordcount

    def getWordLength(self, word):
        return self.wordlen[word]

    def getWordCount(self, word):
        return int(self.wordcount.get(word, 0))


################################################################################################################
class LexiconHandler(ContentHandler) :
    def __init__(self, numStatesPerPhoneme=3):
        self.phonemes = []
        self.lemmas = []
        self.numStatesPerPhoneme = numStatesPerPhoneme
        
        self.orth=[]
        self.symbol=0
        self.phon=0
        self.phonScore=-1
        self.cur_index=0
        self.cur_phoneme = []
        self.cur_lemma = {}
        self.curword=""

        self.currSynt = ""
        self.tok = 0
        self.currEval = ""
        
    def startDocument(self):
        pass

    def startElement(self, name, attrs):
        if name == "phoneme":
            self.cur_phoneme = Phoneme()
        elif name == "symbol":
            self.symbol = 1
            self.curword = ""
        elif name == "lemma":
            self.currSynt = ""
            self.currEval = ""
            self.cur_lemma = Lemma()
        elif name == "orth":
            self.orth = 1
            self.curword = ""
        elif name == "phon":
            self.phon = 1
            self.curword = ""
            if "score" in attrs:
                self.phonScore=attrs["score"]
        elif name == "tok":
            self.tok = 1

    def characters(self, characters):
        if self.orth:
            self.curword = self.curword + characters.strip()
        elif self.symbol:
            self.curword = self.curword + characters.strip()
        elif self.phon:
            # fix for multi line phon sequences and truncated parts of phones
            self.curword = re.sub(r'[\s][\s]*'," ",self.curword)
            self.curword = self.curword + characters
            #self.curword = self.curword.strip()
        elif self.tok:
            self.currSynt = self.currSynt + " " + characters.strip()
            self.currSynt = self.currSynt.strip()
            
    def endElement(self,name):
        if name == "phoneme":
            if self.cur_phoneme.symbol == "si":
                self.cur_phoneme.index.append(self.cur_index)
                self.cur_index += 1
            else:
                for i in range(0, self.numStatesPerPhoneme):
                    self.cur_phoneme.index.append(self.cur_index+i)
                self.cur_index += self.numStatesPerPhoneme
            
            self.phonemes.append(self.cur_phoneme)
        elif name == "symbol":
            self.cur_phoneme.symbol = self.curword
            self.symbol=0
        elif name == "lemma":
            if self.currSynt != "":
                self.cur_lemma.synt.append(self.currSynt)
	    if self.currEval != "":
                self.cur_lemma.eval.append(self.currEval)
            self.lemmas.append(self.cur_lemma)
        elif name == "orth":
            self.cur_lemma.orth.append(self.curword)
            #if self.curword == "":
            #    self.cur_lemma.ort = "_empty_"
            self.orth=[]
        elif name == "phon":
            #print "a"+self.curword+"e"
            self.curword = self.curword.strip()
            singlePhomemes=self.curword.split(' ')
	    self.cur_lemma.phon.append(singlePhomemes)
	    self.cur_lemma.phonScore.append(self.phonScore)
            self.phon=0
            self.phonScore=-1
        elif name == "tok":
            self.tok = 0
            
	elif name == "synt":
	    if self.currSynt=="":
		self.currSynt = "_empty_"
	elif name == "eval":
	    if self.currEval=="":
		self.currEval = "_empty_"

    def endDocument(self):
        pass

    def getMixture(self, mixtureIndex):
        for phonem in self.phonemes:
            if (mixtureIndex >= phonem.index[0]) and (mixtureIndex <= phonem.index[-1]):
                return phonem

    def getMixtureIndex(self, symbol, state):
        for phonem in self.phonemes:
            if(phonem.symbol == str(symbol)):
                return phonem.index

    # gets mixture only of first pronunciation
    def getMixturesByPhon(self, symbol):
        if not isinstance(symbol, basestring): #if it is a list
            symbol = symbol[0]
        for phonem in self.phonemes:
            if(phonem.symbol == str(symbol)):
                return phonem.index


    def getLemmaByOrth(self, orth):
        if not isinstance(orth, basestring): #make sure orth is not actually a list
            orth = orth[0]
        for l in self.lemmas:
            if orth in l.orth:
                return l


################################################################################################################
class GlossParserBoston:
    def __init__(self):
        self.verbose=0
        
    def parseGloss(self, dirtyGloss):
        # which patterns should be simplyfied?
        specialCharacter_pattern = re.compile('([a-zA-Z0-9\:\-]*)([ÜüÖöÄäß\.])([a-zA-Z0-9\:\-]*)')
        mouth_pattern = re.compile('([a-zA-Z0-9\:\-]*)(-\([a-zA-Z0-9\:\-]*\))$')
        xref_pattern = re.compile('(x-ref)(-[a-zA-Z0-9\:\-]*)$')
        x_pattern = re.compile('(x)(-[^ref][a-zA-Z0-9\:\-]*)$')
        pl_pattern = re.compile('([a-zA-Z0-9\:\-]*)(-pl)([a-zA-Z0-9\:\-]*)$')
        dash_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\-)$')
        minus_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\-\-)([a-zA-Z0-9\:\-]*)$')
        plus_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\+)([a-zA-Z0-9\:\-]*)$')
        plusplus_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\+\+)([a-zA-Z0-9\:\-]*)$')
        plusplusplus_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\+\+\+)([a-zA-Z0-9\:\-]*)')
        bracket_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\-?\(\*?[a-zA-Z0-9\:\-]*\)\-?)([a-zA-Z0-9\:\-]*)')
        emp_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\-emp)$')
        emph_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\!)([a-zA-Z0-9\:\-]*)(\!)([a-zA-Z0-9\:\-]*)$')
        silence_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\.$)')
        cross_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\#)([a-zA-Z0-9\:\-]*)$')
        part_pattern = re.compile('([a-zA-Z0-9\:\-]*)(part\:)([a-zA-Z0-9\:\-]*)$')
        pre_neu_pattern = re.compile('([a-zA-Z0-9\:\-]*)(neu\:)([a-zA-Z0-9\:\-]*)$')
        post_neu_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\:neu)([a-zA-Z0-9\:\-]*)$')
        pre_identifier_pattern = re.compile('([a-zA-Z0-9\:\-]*)([ijklm]\:)([a-zA-Z0-9\:\-]*)$')
        post_identifier_pattern = re.compile('([a-zA-Z0-9\:\-]*)(\:[ijklm])([a-zA-Z0-9\:\-]*)$')


        ##############################################
        ## ordering of the patterns plays a role !! ##
        ##############################################
       
        #remove whitespaces in some gloss annotations
        glosses = dirtyGloss.split(' ')
        separator = "-"
        properGloss = separator.join(glosses)
        properGloss = properGloss.replace("\"", "'") ## e.g. 'WHAT" -> 'WHAT'
        
        #remove *-pl annotations
        result = pl_pattern.search(properGloss);
        if not result == None :
            if self.verbose:
                print "deleting pl_pattern:", result.group(), "->", result.group(1) + result.group(3)
            properGloss = result.group(1) + result.group(3)
 
        #replace special characters
        result = specialCharacter_pattern.search(properGloss);
        if not result == None :
            result=re.sub('Ü','UE',properGloss)
            result=re.sub('ü','ue',result)    
            result=re.sub('Ö','OE',result)
            result=re.sub('ö','oe',result)    
            result=re.sub('Ä','AE',result)
            result=re.sub('ä','ae',result)    
            result=re.sub('ß','SS',result)
            result=re.sub('\.','-',result) #silence symbol in SPRINT
            if self.verbose:
                print "replacing specialCharacter_pattern:", properGloss, "->", result
            properGloss = result

##        #remove *-- annotations
##        result = minus_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting minus_pattern:", result.group(), "->", properGloss

##        #remove !*! annotations
##        result = emph_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3) + result.group(5)
##            if self.verbose:
##                print "deleting emph_pattern:", result.group(), "->", properGloss

##        #remove # annotations
##        result = cross_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting cross_pattern:", result.group(), "->", properGloss

##        #remove part: annotations
##        result = part_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting part_pattern:", result.group(), "->", properGloss

##        #remove pre neu: annotations
##        result = pre_neu_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting pre_neu_pattern:", result.group(), "->", properGloss

##        #remove post neu: annotations
##        result = post_neu_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting post_neu_pattern:", result.group(), "->", properGloss

##        #remove [id]: annotations
##        result = pre_identifier_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting pre_identifier_pattern:", result.group(), "->", properGloss

##        #remove :[id] annotations
##        result = post_identifier_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting post_identifier_pattern:", result.group(), "->", properGloss

##        #remove *+++ annotations
##        result = plusplusplus_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting plusplusplus_pattern:", result.group(), "->", properGloss

##        #remove *++ annotations
##        result = plusplus_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting plusplus_pattern:", result.group(), "->", properGloss

##        #remove *+ annotations
##        result = plus_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1) + result.group(3)
##            if self.verbose:
##                print "deleting plus_pattern:", result.group(), "->", properGloss

##        #remove *- annotations (!!!must be placed in last position!!!)
##        result = dash_pattern.search(properGloss);
##        if not result == None :
##            properGloss = result.group(1)
##            if self.verbose:
##                print "deleting dash_pattern:", result.group(), "->", properGloss




        ################################################################
        # SINGLETON HANDLING
        # replace special words -- should maybe done by specifying a list
        ix_pattern = re.compile('(IX)$')
        result = ix_pattern.search(properGloss);
        if not result == None :
            properGloss = result.group(1) + "-2p"
            if self.verbose:
                print "replacing ix_pattern:", result.group(), "->", properGloss
                
        john_pattern = re.compile('(JOHN)$')
        result = john_pattern.search(properGloss);
        if not result == None :
            properGloss = "fs-" + result.group(1)
            if self.verbose:
                print "replacing john_pattern:", result.group(), "->", properGloss

        poss_pattern = re.compile('(POSS)$')
        result = poss_pattern.search(properGloss);
        if not result == None :
            properGloss = result.group(1) + "-3p"
            if self.verbose:
                print "replacing poss_pattern:", result.group(), "->", properGloss

        # todo: gloss length handling?? -> replace list with lookup table might be better
                
        properGloss = properGloss.replace("'WHAT'", "WHAT")
        properGloss = properGloss.replace("(1h)WHAT", "WHAT")
        properGloss = properGloss.replace("(Y)NOT-LIKE", "NOT-LIKE")
        properGloss = properGloss.replace("IX-LOC", "IX-loc")
        properGloss = properGloss.replace("IX-loc:arc", "IX-loc-arc")
        properGloss = properGloss.replace("IX-1p-2:x", "IX-1p")        # only 1 or 3 p
        properGloss = properGloss.replace("THUMB-IX-3p", "IX-3p")
        properGloss = properGloss.replace("IX-3p-pl-arc->-i", "IX-3p-arc")
        properGloss = properGloss.replace("POSS-2p", "POSS-3p")        # only 1 or 3 p
        properGloss = properGloss.replace("GIFT-distributive-3p-arc", "GIFT-distributive")
        properGloss = properGloss.replace("GIFT-3p-arc", "GIFT-arc")
        properGloss = properGloss.replace("neu:GIFT:i", "GIFT")
        properGloss = properGloss.replace("GIVE-3p-arc", "GIFT-arc")   #!
        properGloss = properGloss.replace("fs:JOHN", "fs-JOHN")
        properGloss = properGloss.replace("(1h)CAR", "CAR")
        properGloss = properGloss.replace("(1h)TEACHER", "TEACHER")
        properGloss = properGloss.replace("(1h)DCL:B'hair-on-head-raising'", "DCL:hair-on-head-raising")
        properGloss = properGloss.replace("(2h)DCL:B'hair-on-head-raising'", "DCL:hair-on-head-raising")
        properGloss = properGloss.replace("(2h)NOT^KNOW", "NOT^KNOW")
        properGloss = properGloss.replace("(2h)NOT-YET", "NOT-YET")
        properGloss = properGloss.replace("(2h)SHOULD", "SHOULD")
        #properGloss = properGloss.replace("SHOULD^NOT", "SHOULD NOT") ## cannot split into 2 glosses here ...
        properGloss = properGloss.replace("(2h)VOMIT", "VOMIT")
        properGloss = properGloss.replace("(2h)GIVE-indef", "GIVE-indef")
        properGloss = properGloss.replace("(V)FUTURE", "FUTURE")
        properGloss = properGloss.replace("WILL", "FUTURE")
        properGloss = properGloss.replace("FIND/FIND-OUT", "FIND-OUT")
        properGloss = properGloss.replace("SOMEONE/THING", "SOMETHING/ONE")
        properGloss = properGloss.replace("OVER/AFTER", "AFTER")
        properGloss = properGloss.replace("MOTHER-wg", "MOTHERwg")
        properGloss = properGloss.replace("DO-DO", "DO")
        #properGloss = properGloss.replace("FOR-FOR", "FOR")
        properGloss = properGloss.replace("INFORMATION", "INFORM")

        #######
        #debug
        #
        
        properGloss = properGloss.replace("5'attitude-marker'", "attitude-marker")
        properGloss = properGloss.replace("5'doesn't-matter'", "doesn-t-matter")
        properGloss = properGloss.replace("5'so,-all-set'", "so-all-set")
        
        properGloss = properGloss.replace("BCL:5'raise-hand'", "raise-hand")
        properGloss = properGloss.replace("BCL:5'touch-pocket'", "touch-pocket")

        properGloss = properGloss.replace("DCL:B'across'", "B-across")
        properGloss = properGloss.replace("DCL:G'across'", "G-across")
        properGloss = properGloss.replace("DCL:B'hair-on-head-raising'", "hair-on-head-raising")

        properGloss = properGloss.replace("LCL:5'moving-across'", "moving-across")
        properGloss = properGloss.replace("LCL:B'moving-downwards-at-angle'", "moving-downwards-at-angle")
        properGloss = properGloss.replace("LCL:crvd-V'sitting-on-ground'", "sitting-on-ground")
        properGloss = properGloss.replace("PCL:crvd-5'group-together'", "group-together")

        properGloss = properGloss.replace("SCL:1'person-walking-away'", "person-walking-away")
        properGloss = properGloss.replace("SCL:3'vehicle-pulling-over-vehicle'", "vehicle-pulling-over-vehicle")
        properGloss = properGloss.replace("SCL:3'vehicle-sink'", "vehicle-sink")
        properGloss = properGloss.replace("SCL:B'boat-sink'", "boat-sink")
        properGloss = properGloss.replace("SCL:bent-V'person-sitting-on-ground'", "person-sitting-on-ground")

        properGloss = properGloss.replace("'count-on-fingers'", "count-on-fingers")
        properGloss = properGloss.replace("'um'", "um")
        
        properGloss = properGloss.replace("(1h)", "1h-")
        properGloss = properGloss.replace("(F)", "F-")
        properGloss = properGloss.replace("(L)", "L-")
        properGloss = properGloss.replace("(V)", "V-")
        properGloss = properGloss.replace("(2h)", "2h-")
        properGloss = properGloss.replace("(Y)",  "Y-")
        properGloss = properGloss.replace("(25)", "25-")
        
        #should be placed in last position
        properGloss = properGloss.replace("^", "-con-")
        properGloss = properGloss.replace("'", "-")
        properGloss = properGloss.replace("/", "-or-")
        
        #
        #
        #######
        
        return properGloss

