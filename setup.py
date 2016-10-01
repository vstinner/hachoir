#!/usr/bin/env python3
#
# Procedure to release Hachoir:
#
#  - check version: hachoir/version.py and doc/conf.py
#  - run: ./runtests.py
#  - edit doc/changelog.rst (set release date)
#  - run: hg commit
#  - run: hg tag hachoir-XXX
#  - run: hg push
#  - run: ./README.py
#  - run: ./setup.py --setuptools register sdist upload
#  - run: rm README
#  - check http://pypi.python.org/pypi/hachoir
#  - update doc/install.rst
#  - set version to N+1: hachoir/version.py and doc/conf.py

from imp import load_source
from os import path
from sys import argv
from setuptools import find_packages

SCRIPTS = [
    "hachoir-grep",
    "hachoir-metadata",
    "hachoir-strip",
    "hachoir-subfile",
    "hachoir-urwid",
]

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'Environment :: Plugins',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
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
    if "--setuptools" in argv:
        argv.remove("--setuptools")
        from setuptools import setup
        use_setuptools = True
    else:
        from distutils.core import setup
        use_setuptools = False

    hachoir = load_source("version", path.join("hachoir", "version.py"))

    readme = open('README')
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
    }
    if use_setuptools:
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()
