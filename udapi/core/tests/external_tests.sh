#!/bin/bash
set -e

udapy read.Conllu files=data/UD_Czech_sample.conllu write.Conllu print_sent_id=0 print_text=0 > out.conllu && diff data/UD_Czech_sample.conllu out.conllu && rm out.conllu

cat data/babinsky.conllu | udapy -s > out.conllu && diff data/babinsky.conllu out.conllu && rm out.conllu