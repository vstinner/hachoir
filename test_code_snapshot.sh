#!/bin/bash

# Script to test all Hachoir programs
# You can specify your testcase directory or your Python version with:
#
# PYTHON=python2.5 TESTCASE=~/testcase ./testall.sh

ROOT=$(cd $(dirname $0); pwd)
export PYTHONPATH=$PYTHONPATH:$ROOT
if [ "x$PYTHON" == "x" ]; then
    PYTHON=python
fi
if [ "x$TESTCASE" == "x" ]; then
    TESTCASE=$ROOT/testcase
fi

echo "=== download and check testcase ==="
$PYTHON $ROOT/download_testcase.py $TESTCASE || exit $?

echo "=== hachoir-parser: testcase ==="
$PYTHON $ROOT/test_parser.py $TESTCASE || exit $?

echo "=== hachoir-metadata: testcase ==="
$PYTHON $ROOT/test_metadata.py $TESTCASE || exit $?

