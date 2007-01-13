#!/bin/bash
if [ "x$PYTHON" == "x" ]; then
    PYTHON=python
fi
if [ "x$TESTCASE" == "x" ]; then
    TESTCASE=~/testcase/
fi
ROOT=$(cd $(dirname $0); pwd)

echo "=== hachoir-core: test doc ==="
cd $ROOT/hachoir-core
$PYTHON test_doc.py || exit $?

echo "=== download and check testcase ==="
$PYTHON $ROOT/hachoir-parser/tests/download_testcase.py $TESTCASE || exit $?

echo "=== hachoir-parser: testcase ==="
$PYTHON $ROOT/hachoir-parser/tests/run_testcase.py $TESTCASE || exit $?

echo "=== hachoir-metadata: testcase ==="
$PYTHON $ROOT/hachoir-metadata/run_testcase.py $TESTCASE || exit $?

