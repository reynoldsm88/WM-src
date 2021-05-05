#!/bin/bash

CORENLP_DIST=./distro/stanford-corenlp-4.2.0.zip

if [ -f $CORENLP_DIST ]; then
  echo 'using chached CoreNLP package'
else
    echo "no corenlp distro!!!"
#    mkdir -p distro
#    curl -L -o ./distro/stanford-corenlp-4.2.0.zip http://nlp.stanford.edu/software/stanford-corenlp-4.2.0.zip
fi

docker build -t sofia:latest .
