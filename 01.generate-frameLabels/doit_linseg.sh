#!/bin/bash -xv

it=1

./createDnnTrainingLabels.py --lexiconfile `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --states `grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --corpus `grep shared-train-corpus shared.config | cut -d"=" -f2 | tr -d " "` --borderSilence=1 --midSilence=0 --images `grep shared-train-imageFolder shared.config | cut -d"=" -f2 | tr -d " "`/ --output data/it${it}.train.framelabels --useOne

./createDnnTrainingLabels.py --lexiconfile `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --states `grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --corpus `grep shared-val-corpus shared.config | cut -d"=" -f2 | tr -d " "` --borderSilence=1 --midSilence=0 --images `grep shared-val-imageFolder shared.config | cut -d"=" -f2 | tr -d " "`/ --output data/it${it}.dev.framelabels --useOne

./createDnnTrainingLabels.py --lexiconfile `grep shared-lexicon-file shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --states `grep shared-states shared.config | cut -d"=" -f2 | tr -d " " | tr "\n" "," | sed -e 's,\,$,\n,g'` --corpus `grep shared-orig-test-corpus-file shared.config | cut -d"=" -f2 | tr -d " "` --borderSilence=1 --midSilence=0 --images `grep shared-test-imageFolder shared.config | cut -d"=" -f2 | tr -d " "`/ --output data/it${it}.test.framelabels --useOne





