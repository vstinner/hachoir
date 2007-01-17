#!/bin/bash

TEST_FILES=/home/haypo/mytestcase/ExifTool/
TEST_FILES=~/waves
TEST_FILES=~/mytestcase2/Metadata
TEST_FILES=~/mytestcase2
TEST_FILES=~/testcase
GOTCHA=$PWD/error
MANGLE=$PWD/mangle
MAX_BLOCK=1000
PROG="hachoir-metadata --quiet"
MAX_BLOCK=5000
PROG="hachoir-grep --all --quiet"

if [ ! -e $MANGLE ]; then
    echo "compile mangle..."
    gcc mangle.c -o $MANGLE
    echo "compile mangle... done"
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

if [ "x$PWD" = "x$TEST_FILES" ]; then
    echo "ERROR: don't run $0 in $TEST_FILES directory (or your files will be removed)"
fi

FILE="/tmp/stres-hachoir"
trap 'rm -f "$FILE" ; exit 0' INT

NBERROR=0
while true
do
	while true
	do
		#INFILE=`(find $TEST_FILES -maxdepth 1 -type f) | perl -ne'rand($.)<=1&&($r=$_);END{print$r}'`
		INFILE=`find $HOME/mytestcase -type f -size -50000000 -size +1 | perl -ne'rand($.)<=1&&($r=$_);END{print$r}'`
                echo "total: $NBERROR error -- test file: "$(basename "$INFILE")
		dd if="$INFILE" of="$FILE" count=$MAX_BLOCK 2>/dev/null && \
		$MANGLE "$FILE" $(wc -c "$FILE") && \
		$PROG "$FILE" 2>&1 > /dev/null \
		| grep -q Traceback && break
		rm "$FILE"
	done
        NBERROR=$(expr $NBERROR + 1)
	SHA=`sha1sum "$FILE" | awk '{print $1}'`
        ERRNAME="$SHA-"$(basename "$INFILE")
	mv "$FILE" "$GOTCHA/$ERRNAME"
	echo "=> ERROR: $ERRNAME"
done

