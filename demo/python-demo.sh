#!/bin/bash

export PATH=../bin:$PATH
export PYTHONPATH=../:$PYTHONPATH

udapy read.Conllu filename=en-sample.conllu demo.RehangPrepositions write.Conllu > prepositions-up.conllu
