#!/bin/bash

udapy read.Conllu filename=data/UD_Czech_sample.conllu write.Conllu > out.conllu && diff data/UD_Czech_sample.conllu out.conllu
