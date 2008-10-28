#!/bin/bash
set -e
set -x
rm -rf dist build
./README.py >| README
./setup.py register
./setup.py --setuptools sdist bdist_egg upload
