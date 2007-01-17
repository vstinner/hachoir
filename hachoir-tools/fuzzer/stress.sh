#!/bin/bash

TEST_FILES=/home/haypo/mytestcase/ExifTool/
TEST_FILES=~/mytestcase
TEST_FILES=~/waves
TEST_FILES=~/mytestcase2/Metadata
TEST_FILES=~/mytestcase2
TEST_FILES=~/testcase
GOTCHA=$PWD/error
MANGLE=$PWD/mangle
PROG="hachoir-grep --all --quiet"
MAX_BLOCK=1000
PROG="hachoir-metadata --quiet"
MAX_BLOCK=100

if [ ! -e $MANGLE ]; then
    gcc mangle.c -o $MANGLE
fi

if [ ! -e $GOTCHA ]; then
    echo "mkdir $GOTCHA"
    mkdir -p $GOTCHA
fi

if [ $(find $TEST_FILES -maxdepth 1 -type f|wc -l) -eq 0 ]; then
    echo "Empty directory $TEST_FILES"
    exit 1
fi

# Nice
snice 19

trap 'rm -f "$FILE" ; exit 0' INT

i=0
while true
do
	while true
	do
		FILE=`(cd $TEST_FILES; find . -maxdepth 1 -type f) | perl -ne'rand($.)<=1&&($r=$_);END{print$r}'`
                FILE=$(basename "$FILE")
                echo "total: "$(ls $GOTCHA|wc -l)" error -- test file: $FILE"
		dd if="$TEST_FILES/$FILE" of="$FILE" count=$MAX_BLOCK 2>/dev/null && \
		$MANGLE "$FILE" $(wc -c "$FILE") && \
		$PROG "$FILE" 2>&1 > /dev/null \
		| grep -q Traceback && break
		rm "$FILE"
	done
	((i=$i+1))
	SHA=`sha1sum "$FILE" | awk '{print $1}'`
	mv "$FILE" "$GOTCHA/$SHA"
	echo "=> ERROR: $FILE"
done

