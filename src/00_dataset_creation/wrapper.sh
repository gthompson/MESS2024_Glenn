#!/bin/bash
srcdir=$(dirname -- "$0")
cd $srcdir
python ../setup_paths.py
for FILE in `ls ./0*.py | sort -g`; do
    echo "$FILE";
    python "$FILE";
done
