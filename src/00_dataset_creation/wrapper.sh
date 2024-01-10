#!/bin/bash
srcdir=$(dirname -- "$0")
cd $srcdir
for FILE in `ls ./0*.py | sort -g`; do
    python "$FILE";
done
