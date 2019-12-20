from string import split, join

################################################################################################################
class Recording:
    def __init__(self):
        self.name    = ""
        self.video   = ""
        self.start   = -1 #0.0
        self.end     = -1 #0.0
        self.speaker = ""
        self.descriptions = []
        self.orth    = []
        self.translation = ""
        self.score   = 0.0

    def __cmp__(self, other):
        return cmp(self.score, other.score)

    def __str__(self):
        return "record: name=%s, video=%s, start=%s, end=%s, speaker=%s, orth=%s, translation=%s" \
               % (self.name, self.video, self.start, self.end, self.speaker, self.orth, self.translation)

    def CSVheader(self, outputDelimiter=";",addTranslation=False):
        msg = "name"+outputDelimiter+"video"+outputDelimiter+"start"+outputDelimiter+"end"+outputDelimiter+"speaker"+outputDelimiter+"orth"
        if addTranslation:
            msg += outputDelimiter+"translation"
        return msg
    
        
    def CSVrecording(self, outputDelimiter=";",addTranslation=False):
        msg = "%s%s%s%s%s%s%s%s%s%s%s" % (self.name, outputDelimiter, self.video, outputDelimiter, self.start, outputDelimiter, self.end, outputDelimiter, self.speaker, outputDelimiter, join(self.orth))
        if addTranslation:
            msg += "%s%s" % (outputDelimiter, self.translation)
        return msg
##        return "%s%s%s%s%s%s%s%s%s%s%s%s%s%s" \
##               % (self.name, outputDelimiter, self.video, outputDelimiter, self.start, outputDelimiter, self.end, outputDelimiter, self.speaker, outputDelimiter, join(self.orth), outputDelimiter, self.translation, outputDelimiter)


################################################################################################################
class Speaker:
    def __init__(self):
        self.name    = ""
        self.gender  = ""

    def __str__(self):
        return "name: '%s', gender: '%s'" % (self.name, self.gender)


################################################################################################################
class Phoneme:
    def __init__(self):
        self.symbol = ""
        self.index  = []

    def __str__(self):
        return self.symbol

    def __cmp__(self, other):
        return cmp(self.symbol, other.symbol)


################################################################################################################
class Lemma:
    def __init__(self):
        self.orth = []
        self.phon = []
        self.phonScore = []
        self.eval = []
        self.synt = []

    def __str__(self):
        return "orth: '%s', phon: '%s'" % (" ".join(self.orth), ", ".join([" ".join(inner) for inner in self.phon]))



################################################################################################################
class FieldAnnotation:
    def __init__(self, _id, _name):
        self.id    = _id
        self.name  = _name
        self.value = []

    def __str__(self):
        return "field id: %d, name: %s, value: '%s'" \
               % (self.id, self.name, self.value)


################################################################################################################
class MediaFileAnnotation:
    def __init__(self, _id, _path, _cameratype):
        self.id          = _id
        self.path        = _path
        self.cameratype  = _cameratype

    def __str__(self):
        return "media-file id: %d, path: %s, cameratype: %s" \
               % (self.id, self.path, self.cameratype)


################################################################################################################
class Utterance:
    def __init__(self, _id, _excerpt, _start, _end, _notes=""):
        self.id          = _id
        self.notes       = _notes
        self.excerpt     = _excerpt
        self.start       = _start
        self.end         = _end
        self.medias      = []
        self.segments    = []

    def __str__(self):
        ret = "utterance id: %d, notes: %s, excerpt: %s, start: %d, end: %d, medias: %s, segments: \n" \
               % (self.id, self.notes, self.excerpt, self.start, self.end, self.medias)
        for segment in self.segments:
            ret += "  * %s \n" % (segment)
        return ret


################################################################################################################
class Segment:
    def __init__(self, _id):
        self.id      = _id
        self.tracks  = []

    def __str__(self):
        ret = "segment id: %d, tracks: \n" % (self.id, )
        for track in self.tracks:
            ret += "    * %s \n" % (track)
        return ret


################################################################################################################
class Video:
    def __init__(self, name, frames, filename = ""):
        self.name = name
        self.frames = frames
        self.filename = filename
        self.segments = []  #@todo: should provide an associative array access {} self.segments[segment.id]
        self.speaker = ""
    def __str__(self):
        ret = "video: name '%s', filename '%s', speaker '%s'\n" % (self.name, self.filename, self.speaker)
        for frame in self.frames:
            ret += " * %s \n" % (frame)
        for segment in self.segments:
            ret += " * %s \n" % (segment)
        return ret


################################################################################################################
class Frame:
    def __init__(self, framenr, file):
        self.framenr = framenr
        self.file = file
    def __str__(self):
        return "frame: framenr %d, file %s" % (self.framenr, self.file)


################################################################################################################
class Track:
    def __init__(self, _id):
        self.id           = _id
        self.annotations  = []

    def __str__(self):
        ret = "track id: %d, annotations: \n" \
              % (self.id, )
        for annotation in self.annotations:
            ret += "      * %s \n" % (annotation)
        return ret


################################################################################################################
class Annotation:
    def __init__(self, _start=-1, _end=-1, _vid="unknown"):
        self.start      = _start
        self.end        = _end
        self.vid        = _vid
        self.value      = ""

    def __str__(self):
        return "start: %d, end: %d, vid: %d, annotation: %s" \
               % (self.start, self.end, self.vid, self.value)


################################################################################################################
class Participant:
    def __init__(self, _id, _name, _label, _age, _gender, _language):
        self.id       = _id
        self.name     = _name
        self.label    = _label
        self.age      = _age
        self.gender   = _gender
        self.language = _language

    def __str__(self):
        return "participant id: %d, name: %s, label: %s, age: %d, gender: %s, language: %s" \
               % (self.id, self.name, self.label, self.age, self.gender, self.language)


################################################################################################################
class Pronunciation:
    def __init__(self, orth, pronunciations):
        self.orth            = orth
        self.pronunciations  = pronunciations

    def __str__(self):
        return "pronunciation orth: %s, pronunciations: %s" % (self.orth, join(self.pronunciations))

