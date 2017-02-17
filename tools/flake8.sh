#!/bin/sh
set -e -x
cd $(dirname "$0")/..
# use /bin/sh to support "*.py"
# FIXME: add hachoir-wx (currrently broken)
flake8 hachoir/ tests/ runtests.py setup.py doc/examples/*.py
