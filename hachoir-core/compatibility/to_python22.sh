#!/bin/bash

MV=`which mv`
RM=`which rm`
PYTHON=`which python2.4`
WGET=`which wget`
COMPAT=$(cd $(dirname $0); pwd)
ROOT=$(cd $COMPAT/..; pwd)
PYPY_DATETIME=https://codespeak.net/viewvc/pypy/dist/pypy/lib/datetime.py?revision=HEAD

MODULE=datetime.py
if ! test -e $ROOT/$MODULE; then
  echo "Download $MODULE from PyPy"
  $WGET -O $ROOT/$MODULE $PYPY_DATETIME || { $RM $ROOT/$MODULE; exit 1; }
fi

if test "$1x" != "NOCHECKx"; then
    $COMPAT/revert_all.sh || exit $?
fi

cd $ROOT
patch -p0 < $COMPAT/to_python22.patch
$COMPAT/to_python23.sh NOCHECK

cd $ROOT
echo "*** ADD sum() function to all Python scripts (at the second line) ***"
for file in $(grep -l sum $(ls script/* $(find -name "*.py"))|egrep -v '(check_interpreter|datetime|compatibility)'); do
    head -n 1 "$file" >"$file.new"
    cat >>"$file.new" <<EOF
import operator
def sum(datas):
    return reduce(operator.add, datas)
EOF
    tail -n +2 "$file" >>"$file.new"
    $MV "$file.new" "$file"
done

