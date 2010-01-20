#!/bin/sh

set -e

[ "$PYTHON"   ] || PYTHON=python
[ "$TESTCASE" ] || TESTCASE=~/testcase/

ROOT=$(cd $(dirname $0); pwd)

source $ROOT/setupenv.sh

echo "=== hachoir-core: test doc ==="
cd $ROOT/hachoir-core
$PYTHON test_doc.py

echo "=== download and check testcase ==="
$PYTHON $ROOT/hachoir-parser/tests/download_testcase.py $TESTCASE

echo "=== hachoir-parser: testcase ==="
$PYTHON $ROOT/hachoir-parser/tests/run_testcase.py $TESTCASE

echo "=== hachoir-metadata: testcase ==="
$PYTHON $ROOT/hachoir-metadata/test_doc.py

echo "=== hachoir-metadata: testcase ==="
$PYTHON $ROOT/hachoir-metadata/run_testcase.py $TESTCASE

echo "=== hachoir-regex: tests ==="
$PYTHON $ROOT/hachoir-regex/test_doc.py
