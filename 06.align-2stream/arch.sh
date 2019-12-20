#! /bin/bash

unset LD_LIBRARY_PATH;
ARCHEX=""
if [ ${ARCH} == "x86_64" ]; then
    ARCHEX="64"
fi
export LD_LIBRARY_PATH=:${HOME}/lib_${ARCH}:/usr/lib${ARCHEX}:/work/speech/tools/openfst-1.2.R/lib
export PKG_CONFIG_PATH=/usr/lib/pkgconfig/:${HOME}/lib_${ARCH}/pkgconfig
export FFMPEG_VERSION=52
executable=linux-intel-standard
if [ ${ARCH} == "x86_64" ]; then
  executable=linux-x86_64-standard
fi

export SGE_TASK_ID=`printf %04d ${SGE_TASK_ID}`
