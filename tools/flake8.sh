#!/bin/sh
set -e -x
cd $(dirname "$0")/..
# use /bin/sh to support "*.py"
# FIXME: add hachoir-wx (currrently broken)
flake8 \
    hachoir/ tests/ \
    runtests.py setup.py \
    hachoir-{grep,metadata,metadata-csv,metadata-gtk,metadata-qt,strip,subfile,urwid} \
    doc/examples/*.py
