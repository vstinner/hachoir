#!/bin/sh
# Convert Hachoir source code to Python for Jython 2.2

PYPY_PYTHONLIB_SVN=https://codespeak.net/viewvc/pypy/dist/lib-python/2.4.1
COMPAT=$(cd $(dirname $0); pwd)
ROOT=$(cd $COMPAT/..; pwd)
RM=`which rm`
WGET=`which wget`

for MODULE in gettext optparse textwrap; do
    if ! test -e $ROOT/$MODULE.py; then
      echo "Download $MODULE.py from Python library of PyPy"
      $WGET -O $ROOT/$MODULE.py $PYPY_PYTHONLIB_SVN/$MODULE.py?revision=HEAD || { $RM $ROOT/$MODULE.py; exit 1; }
      if test "x$MODULE" = "xgettext"; then
          (cd $ROOT; patch -p0 < $COMPAT/jython_gettext.patch)
      fi
    fi
done

$COMPAT/revert_all.sh || exit $?

cd $ROOT
patch -p0 < $COMPAT/jython.patch
$COMPAT/to_python23.sh NOCHECK jython

