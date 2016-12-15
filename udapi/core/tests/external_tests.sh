#!/bin/bash

udapy read.Conllu filename=UD_Czech_sample.conllu write.Conllu > out.conllu && diff UD_Czech_sample.conllu out.conllu
