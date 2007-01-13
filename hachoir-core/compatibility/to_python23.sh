#!/bin/bash

MV=/bin/mv
PYTHON=`which python2.4`
COMPAT=$(cd $(dirname $0); pwd)
ROOT=$(cd $COMPAT/..; pwd)
CONVERTER=$COMPAT/to_python23.py

if test "$1x" != "NOCHECKx"; then
    CONVERT_TO=$1
    $COMPAT/revert_all.sh || exit $?
else
    CONVERT_TO=$2
fi

cd $ROOT
patch -p0 < $COMPAT/to_python23.patch
for file in $(ls script/* $(find . -name "*.py")\
|egrep -v '(check_interpreter|datetime|compatibility)'); do
    $PYTHON $CONVERTER <"$file" >"$file.new" $CONVERT_TO || exit $?
    $MV "$file.new" "$file"
done

