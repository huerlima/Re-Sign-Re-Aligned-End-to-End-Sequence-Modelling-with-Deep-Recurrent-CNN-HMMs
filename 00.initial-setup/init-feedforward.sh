#!/bin/bash

trainCorpus=`grep shared-orig-corpus-file config/shared.config | cut -d '=' -f 2 | tr -d ' '`
devCorpus=`grep shared-orig-val-corpus-file config/shared.config | cut -d '=' -f 2 | tr -d ' '`
corpusname=`grep shared-corpusname config/shared.config | cut -d '=' -f 2 | tr -d ' '`


trainRecordings=`grep shared-orig-corpus-file config/shared.config | cut -d '=' -f 2 | tr -d ' ' | sed -e 's,corpus$,recordings,g'`
trainSpeaker=`grep shared-orig-corpus-file config/shared.config | cut -d '=' -f 2 | tr -d ' ' | sed -e 's,corpus$,speaker,g'`

cat $trainSpeaker $trainRecordings | tr "\n" "%" | sed -e 's,</corpus>%<?xml version="1.0" encoding="utf-8"?>%<corpus name="'$corpusname'">%,,g' | sed -e 's,%,\n,g' > data/it0.train.corpus

valRecordings=`grep shared-orig-val-corpus-file config/shared.config | cut -d '=' -f 2 | tr -d ' ' | sed -e 's,corpus$,recordings,g'`
valSpeaker=`grep shared-orig-val-corpus-file config/shared.config | cut -d '=' -f 2 | tr -d ' ' | sed -e 's,corpus$,speaker,g'`

cat $valSpeaker $valRecordings | tr "\n" "%" | sed -e 's,</corpus>%<?xml version="1.0" encoding="utf-8"?>%<corpus name="'$corpusname'">%,,g' | sed -e 's,%,\n,g' > data/it0.val.corpus

lexicon=`grep shared-lexicon-source-file config/shared.config | cut -d '=' -f 2 | tr -d ' '`

cp $lexicon data/it0.stream-0.lex

