import csv
import os
import random
import h5py
import numpy as np
import sys

if len(sys.argv) <1:
	exit("Usage: <it>")

def add2h5(h, target_labels_fname):
	#read labels from txt file
	with open(target_labels_fname) as f :
                target_labels = csv.reader(f, delimiter=' ')
                target_labels = list(target_labels)

		#labels= [float(i[1]) for i in labels]
		sentences= [ i[0][::-1].split('/')[1][::-1] for i in target_labels ]
                target_labels= [float(i[1]) for i in target_labels]
		cont = [float(0) if (sentences[i]!=sentences[i-1] or target_labels[i]<0) else float(1) for i in range(len(sentences))]

	#convert to np array
	cont = np.asarray(cont, dtype=np.float64)
	cont = cont.reshape(cont.shape[0],1) # going from 1D x data-shape to 2D x,1

        #convert to np array
        target_labels = np.asarray(target_labels, dtype=np.float64)
        target_labels = target_labels.reshape(target_labels.shape[0],1) # going from 1D x data-shape to 2D x,1

        dset = h.create_dataset('label-0', data=target_labels)  #write to file
        dset = h.create_dataset('cont', data=cont) #write to file
        dset = h.create_dataset('sentences', data=sentences)        #write to file


it=sys.argv[1]
set=sys.argv[2]

target_label_file='data/it'+it+'.'+set+'.framelabels'

dest='data/it'+it+'.hdf5/it'+it+'_'+set+'.h5'

print target_label_file

h = h5py.File(dest, 'w')
add2h5(h, target_label_file)

