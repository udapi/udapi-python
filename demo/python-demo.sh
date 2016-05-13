#!/usr/bin/bash

export PATH=../python/bin:$PATH
export PYTHONPATH=../python/:$PYTHONPATH

udapi.py read.Conllu filename=sample.conllu Dummy write.Conllu > prepositions-up.conllu
