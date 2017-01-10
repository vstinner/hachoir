#!/usr/bin/env python3
#
# Prepare a release:
#
#  - check version: hachoir/version.py and doc/conf.py
#  - run tests: tox
#  - set the release date: edit doc/changelog.rst
#  - run: git commit -a
#  - run: git push
#  - check Travis CI status:
#    https://travis-ci.org/haypo/hachoir3
#
# Release a new version:
#
#  - run: git tag x.y.z
#  - run: git push --tags
#  - rm -rf dist/
#  - run: python3 setup.py sdist bdist_wheel
#  - FIXME: register? twine register dist/hachoir-x.y.z.tar.gz
#  - twine upload dist/*
#  - check http://pypi.python.org/pypi/hachoir3
#
# After the release:
#
#  - update doc/install.rst
#  - set version to N+1: hachoir/version.py and doc/conf.py

from imp import load_source
from os import path
from setuptools import find_packages

SCRIPTS = ["hachoir-grep",
           "hachoir-metadata",
           "hachoir-strip",
           "hachoir-urwid",
           "hachoir-wx"]
# FIXME: hachoir-subfile is currently broken
# "hachoir-subfile",

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'Environment :: Plugins',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Topic :: Multimedia',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: Software Development :: Disassemblers',
    'Topic :: Software Development :: Interpreters',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System :: Filesystems',
    'Topic :: Text Processing',
    'Topic :: Utilities',
]


def main():
    from setuptools import setup

    hachoir = load_source("version", path.join("hachoir", "version.py"))

    readme = open('README.rst')
    long_description = readme.read()
    readme.close()

    install_options = {
        "name": hachoir.PACKAGE,
        "version": hachoir.VERSION,
        "url": hachoir.WEBSITE,
        "author": "Hachoir team (see AUTHORS file)",
        "description": "Package of Hachoir parsers used to open binary files",
        "long_description": long_description,
        "classifiers": CLASSIFIERS,
        "license": hachoir.LICENSE,
        "packages": find_packages(),
        "scripts": SCRIPTS,
        "zip_safe": True,
    }
    setup(**install_options)


if __name__ == "__main__":
    main()
