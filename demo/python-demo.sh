#!/bin/bash

export PATH=../bin:$PATH
export PYTHONPATH=../python/:$PYTHONPATH

udapy read.Conllu filename=en-sample.conllu Dummy write.Conllu > prepositions-up.conllu
