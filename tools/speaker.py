#!/usr/bin/python
import xml.dom.minidom
from miscLib import uopen, uclose

class Speaker:

	def __init__(self, databaseName, encoding="utf8"):
            self.encoding=encoding
            self.doc = xml.dom.minidom.Document()
            self.root = self.doc.createElement('corpus')
            self.root.setAttribute("name", databaseName)
            self.root.appendChild( self.doc.createComment(" created with createcorpus.py ") )
            self.doc.appendChild(self.root)

	def addSpeakerDescription(self, speakerName, genderName):
#            speakerName = speakerName.encode(self.encoding)
#            genderName = genderName.encode(self.encoding)

            speaker = self.doc.createElement('speaker-description')
            speaker.setAttribute("name", speakerName)

            gender = self.doc.createElement('gender')
            gender.appendChild( self.doc.createTextNode(genderName) )

            speaker.appendChild(gender)            
            self.root.appendChild(speaker)

	def save(self, filename):
            out = uopen(filename,self.encoding,"w")
            self.doc.writexml(out, '', '  ', '\n', 'utf-8')
            uclose(out)
