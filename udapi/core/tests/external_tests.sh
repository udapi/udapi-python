#!/bin/bash
set -e

udapy write.Conllu print_sent_id=0 print_text=0 < data/UD_Czech_sample.conllu > out.conllu && diff data/UD_Czech_sample.conllu out.conllu && rm out.conllu

udapy -s read.Conllu files=data/babinsky.conllu split_docs=1 > out.conllu && diff data/babinsky.conllu out.conllu && rm out.conllu
