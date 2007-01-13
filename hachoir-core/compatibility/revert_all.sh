#!/bin/sh

cd $(dirname $0)/..

M=$(svn stat|grep ^M|cut -d' ' -f7|egrep -v '(revert_all|compatibility|\.patch$)')
if test "x$M" = "x"; then
    echo "Repository is clean (no modification, but may add and remove)"
    exit 0
fi

if test "x$1" = "xREVERTALL"; then
    echo "*** REVERT ALL ***" 1>&2
    svn revert $M
    echo "Revert: done"
    exit 0
else
    echo "Repository is not clean. Clean it using:"
    echo "$0 REVERTALL"
    exit 1
fi

