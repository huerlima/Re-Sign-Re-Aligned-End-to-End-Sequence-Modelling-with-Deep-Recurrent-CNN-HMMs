#!/usr/bin/python
# author:  oscar koller
# date: 2017 03 31

import sys
import progressbar
import os

from google.protobuf import text_format

args=sys.argv
print "\n".join(sys.argv)
from argparse import ArgumentParser

# converts SoftmaxWithLoss layers to Softmax layers and removes the second bottom (i.e. the label)
# other conversions on additional arguments

def getOptions():
        arg_parser = ArgumentParser()
        arg_parser.add_argument("--prototxt", help="the net structure, with which the training was performed")
        arg_parser.add_argument("--hdfsource", help="set the hdf5 source")
        arg_parser.add_argument("--datasource", help="set the data source")
        arg_parser.add_argument("--outproto", default="out.prototxt", help="The name of changed output prototxt file. [out.prototxt]")
        arg_parser.add_argument("--path", default="/work/cv3/zargaran/caffe/caffe-reverselayer-2016_10_19/python/", help="specify the caffe python path [/work/cv3/zargaran/caffe/caffe-reverselayer-2016_10_19/python/]")
        arg_parser.add_argument("-v","--verbose",action="store_true", help="be verbose")
        args = arg_parser.parse_args()
        if len(sys.argv) == 1:
                arg_parser.print_help()
                sys.exit(1)
        return args

def readProto(filepath):
    import caffe

    f = open(filepath, "r")
    prototxtParser = caffe.proto.caffe_pb2.NetParameter()
    text_format.Merge(str(f.read()), prototxtParser)
    #while( hasattr(prototxtParser, "layer") ):
    for  (ind, obj) in enumerate(prototxtParser.layer):
        #print ind, obj.name, obj.type
        if obj.type == "SoftmaxWithLoss":
            del obj.bottom[1]
            obj.type = "Softmax"
        if obj.type == "Data" and args.datasource is not None:
            obj.data_param.source = args.datasource
        if obj.type == "HDF5Data" and args.hdfsource is not None:
            obj.hdf5_data_param.source = args.hdfsource

    #print text_format.MessageToString(prototxtParser)
    f.close
    return prototxtParser
        
def main(argv):
        global args
        args = getOptions()
        
        # Make sure that caffe is on the python path:
        sys.path.append(args.path)

        import caffe
        from caffe.proto import caffe_pb2

        newProto = readProto(args.prototxt)
        # Write the new proto back to disk.
        f = open(args.outproto, "wb")
        f.write(text_format.MessageToString(newProto))
        f.close()
                
if __name__ == "__main__":
    main(sys.argv)
