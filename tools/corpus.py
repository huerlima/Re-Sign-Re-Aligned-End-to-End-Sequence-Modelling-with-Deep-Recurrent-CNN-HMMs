#!/usr/bin/python
# -*- coding: utf-8 -*-
#$Id: corpus.py,v 1.8 2006-11-08 16:05:41 dreuw Exp $
import xml.dom.minidom
import math
import sys
from string import join
from miscLib import uopen, uclose

class Record:
    def __init__(self, name, video, start, end, speaker, orth, translation):
        self.name        = name
        self.video       = video
        self.start       = start
        self.end         = end
        self.speaker     = speaker
        self.orth        = orth
        self.translation = translation
    def __str__(self):
        return "record: name=%s, video=%s, start=%s, end=%s, speaker=%s, orth=%s" \
               % (self.name, self.video, self.start, self.end, self.speaker, self.orth)


def getStartSample(startTime_, sampleRate_) :
    framePrecision=10000
    start = int(startTime_ * framePrecision) * int(sampleRate_);
    if((start % framePrecision) == 1):
        start += framePrecision

    return int(start / framePrecision);


def getEndSample(endTime_, sampleRate_) :
    return int(math.floor(endTime_ * sampleRate_));


def getNumSamples(startTime, endTime, sampleRate) :
    return getEndSample(endTime, sampleRate) - getStartSample(startTime, sampleRate)


def checkStartAndEndTime(startTime_, endTime_, nSamples, sampleRate_=25.0):
    shift         = float(1.0/sampleRate_);
    newStartTime  = float(startTime_);
    newEndTime    = float(endTime_);
    duration      = float(endTime_ - startTime_);
    minDuration   = float(nSamples * shift);
    
    startSample  = getStartSample(startTime_, sampleRate_)
    endSample    = getEndSample(endTime_, sampleRate_)
    #if (endSample <= startSample):
    #    print "warning: endSample <= startSample"
        
    samples = endSample-startSample; ##todo: samples might be negative due to rounding; or use verify
    #print "*** startSample=", startSample, ", endSample=", endSample, ", samples=", samples, ", nSamples=", nSamples

    if(samples < nSamples):
        #print "*** startTime_=", startTime_, ", endTime_=", endTime_
        #print "*** startSample=", startSample, ", endSample=", endSample
        missingSamples = nSamples-samples; ## todo: samples might be negative due to rounding
            
        newStartTime -= float(int((missingSamples/2.0)+0.5) * shift); ## ceil
        newEndTime   += float(int(missingSamples/2.0) * shift);       ## floor
        #print "*** newStartTime=", newStartTime, ", newEndTime=", newEndTime
        
        ##due to rounding there might miss one image, i.e. now duration > minDuration, but one image lost
        if(int(newEndTime * sampleRate_)-int((newStartTime * sampleRate_)+0.5) == nSamples):
            newEndTime += shift;
            #print "*** -1 problem, newEndTime=", newEndTime
                
    if(newStartTime < 0.0):
        print "WARNING: newStartTime < 0.0 [shift=%f, newStartTime=%f, newEndTime=%f, duration=%f, nSamples=%d, minDuration=%f, oldStartTime=%f]\n" \
              % (shift, newStartTime, newEndTime, duration, nSamples, minDuration, float(startTime_))
        newStartTime += shift;
        newEndTime   += shift;
        #sys.exit("error: newStartTime < 0.0, check your settings.")

    return (newStartTime, newEndTime)


class Corpus:

    def __init__(self, databaseName, minSamples=0, samplerate = 25, encoding="utf8"):
            self.encoding=encoding
            self.minSamples=minSamples
            self.doc = xml.dom.minidom.Document()
            self.root = self.doc.createElement('corpus')
            self.root.setAttribute("name", databaseName.encode(self.encoding))
            self.root.appendChild( self.doc.createComment(" created with corpus.py ") )
            self.recordings = {}
            self.samplerate = samplerate
            if self.minSamples > 0:
                self.root.appendChild( self.doc.createComment(" timestamps might differ from original "
                                                              + "eaf files due to minimum-samples option set to '"
                                                              + str(minSamples)
                                                              + "'. ") )
            self.doc.appendChild(self.root)

    def includeFile(self, fileName):
            include = self.doc.createElement('include')
            include.setAttribute("file", fileName.encode(self.encoding))
            self.root.appendChild(include)

    def addSpeakerDescription(self, speakerName, genderName):
            speakerName = speakerName.encode(self.encoding)
            genderName = genderName.encode(self.encoding)

            speaker = self.doc.createElement('speaker-description')
            speaker.setAttribute("name", speakerName)

            gender = self.doc.createElement('gender')
            gender.appendChild( self.doc.createTextNode(genderName) )

            speaker.appendChild(gender)            
            self.root.appendChild(speaker)
                        
    def addRecord(self, record, checkStartEnd = True):
            #print "*** debug: record.translation=", record.translation
            self.addRecording(record.name,
                              record.video,
                              record.start,
                              record.end,
                              record.speaker,
                              join(record.orth, " "),
                              checkStartEnd,
                              record.translation)

    def addRecording(self, recordName, recordVideo, startTime, endTime, speakerName, recordOrth, checkStartEnd = True, recordTranslation = ""):
            recording = self.doc.createElement('recording')
            recording.setAttribute("name", recordName.encode(self.encoding))
            recording.setAttribute("video", recordVideo.encode(self.encoding))
            self.recordings[recordName] = recording
            if recordOrth != None:
                segmentName="1"
                self.addSegment(recordName, startTime, endTime, speakerName, recordOrth, checkStartEnd, recordTranslation, segmentName)
            self.root.appendChild(recording)

    def addSegment(self, recordName, startTime, endTime, speakerName, recordOrth, checkStartEnd, recordTranslation, segmentName):
            segment = self.doc.createElement('segment')
            segment.setAttribute("name",segmentName)
            speaker = self.doc.createElement('speaker')
            speaker.setAttribute("name", speakerName) #speakerName.encode(self.encoding))
            segment.appendChild(speaker)
            startTime = float(startTime)
            endTime   = float(endTime)
            if checkStartEnd and startTime > -1 :
                (startTime, endTime) = checkStartAndEndTime(startTime, endTime, self.minSamples, self.samplerate)
            if startTime > -1:
                segment.setAttribute("start", str(startTime).encode(self.encoding))
            if endTime > -1:
                    segment.setAttribute("end", str(endTime).encode(self.encoding))
            orth = self.doc.createElement('orth')
	    if not isinstance(recordOrth, unicode):
		recordOrth = recordOrth.decode(self.encoding, 'ignore')
            orth.appendChild( self.doc.createTextNode(recordOrth) )
            segment.appendChild(orth)
            #signlanguage sentence won't be used by bliss corpus parser
            if recordTranslation != "":
                translation = self.doc.createElement('translation')
		if not isinstance(recordTranslation, unicode):
                    recordTranslation = recordTranslation.decode(self.encoding, 'ignore')
                translation.appendChild( self.doc.createTextNode(recordTranslation) )
                segment.appendChild(translation)
            self.recordings[recordName].appendChild(segment)
                
    def save(self, filename):
            out = uopen(filename, self.encoding, 'w')
            self.doc.writexml(out, '', '  ', '\n', self.encoding)
            uclose(out)

