import sys
import csv
import time
import re
set= sys.argv[1]
it=sys.argv[2]

garbageIndex=0

with open('data/it'+str(it)+'.'+set+'.framelabels', mode='r') as labelList:
    reader=csv.reader(labelList,delimiter=' ')
    label = {}
    for line in reader:
        line[0] = "/" + line[0]
        tempString = "/".join(line[0].strip('\n').rsplit('/', 4)[1:])
        label[tempString]=line[1]

with open('data/leveldb_shuffle/'+set+'_shuffle.txt', mode='r') as imgList:
    reader=csv.reader(imgList,delimiter=' ')
    for line in reader:
        if line[0] in label:
            print (line[0]+" "+label[line[0]])
        else:
            print (line[0]+" "+str(garbageIndex))

