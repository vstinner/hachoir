#!/bin/bash
ROOT=$(cd $(dirname $0); pwd)
DATE="$(date +"%Y-%m-%d")"
NAME=hachoir-snapshot-$DATE
TMPDIR=/tmp/$NAME

if test $# -eq 0; then
    echo >>/dev/stderr "usage: $0 [--win32] component1 component2 ..."
    echo >>/dev/stderr
    echo >>/dev/stderr "component: metadata, urwid, ... (core and parser are always included)"
    exit 1
fi

echo "[+] Prepare destination"
rm -rf "$TMPDIR"
mkdir -p "$TMPDIR"

WIN32=0
WITHTEST=1
COMPONENTS=""
TOOLS=1
for component in core parser $*; do
    if [ "$component" = "--win32" ]; then
        WIN32=1
    else
        COMPONENTS="$COMPONENTS $component"
    fi
done

for component in $COMPONENTS; do
    echo "[+] svn export hachoir-$component"
    svn export "$ROOT/hachoir-$component/hachoir_$component" "$TMPDIR/hachoir_$component"
    if [ -e "$ROOT/hachoir-$component/hachoir-$component" ]; then
        echo "[+] copy hachoir-$component script"
        if [ $WIN32 -eq 1 ]; then
            cp "$ROOT/hachoir-$component/hachoir-$component" "$TMPDIR/hachoir-$component.py"
        else
            cp "$ROOT/hachoir-$component/hachoir-$component" "$TMPDIR/hachoir-$component"
        fi
    fi
    if [ -e "$ROOT/hachoir-$component/README" ]; then
        echo "[+] copy README.hachoir-$component"
        if [ $WIN32 -eq 1 ]; then
            # TODO: Convert Unix EOL to Windows EOL
            sed -e 's/$/\r/g' "$ROOT/hachoir-$component/README" > "$TMPDIR/README.hachoir-$component.txt"
        else
            cp "$ROOT/hachoir-$component/README" "$TMPDIR/README.hachoir-$component"
        fi
    fi
done

if [ $WIN32 -eq 0 -a $WITHTEST -eq 1 ]; then
    echo "[+] Include tests"
    cp hachoir-parser/tests/download_testcase.py $TMPDIR/
    cp hachoir-parser/tests/run_testcase.py $TMPDIR/test_parser.py
    cp hachoir-metadata/run_testcase.py $TMPDIR/test_metadata.py
    cp test_code_snapshot.sh $TMPDIR/testall.sh
fi

# Include some tools
if [ $TOOLS -eq 1 ]; then
    cp hachoir-tools/hachoir-grep $TMPDIR/
    cp hachoir-tools/hachoir-strip $TMPDIR/
fi

if [ $WIN32 -eq 1 ]; then
    ARCHIVE=$ROOT/$NAME.zip
    rm -f $ARCHIVE
    echo "[+] Create archive $(basename $ARCHIVE)"
    (cd $(dirname $TMPDIR); zip -9 -r $ARCHIVE $(basename $TMPDIR)/)
else
    ARCHIVE=$ROOT/$NAME.tar.bz2
    echo "[+] Create archive $(basename $ARCHIVE)"
    (cd $(dirname $TMPDIR); tar -cjf $ARCHIVE $(basename $TMPDIR)/)
fi

rm -rf $TMPDIR

echo
echo "Done: snapshot is $ARCHIVE"

