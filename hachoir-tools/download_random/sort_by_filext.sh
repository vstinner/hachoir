#!/bin/sh

dbdir="filedb"

if [ "x$1" = "x" ]; then
   echo "usage: $0 directory"
   exit 1
fi

echo "Sort files from $1"

for ext in bmp jpg png gif; do
  dir=$dbdir/$ext
  mkdir -p $dir
  mv $1/*.$ext $dir
done

echo "done"

