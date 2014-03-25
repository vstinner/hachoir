#!/usr/bin/env python3
# Procedure to release a new version:
#  - edit hachoir/version.py: __version__ = "XXX"
#  - run: ./runtests.py
#  - edit ChangeLog (set release date)
#  - run: hg commit
#  - run: hg tag hachoir-XXX
#  - run: hg push
#  - run: ./README.py
#  - run: ./setup.py --setuptools register sdist upload
#  - run: rm README
#  - check http://pypi.python.org/pypi/hachoir-parser
#  - update the website
#    * http://bitbucket.org/haypo/hachoir/wiki/Install/source
#    * http://bitbucket.org/haypo/hachoir/wiki/Home
#  - edit hachoir/version.py: set version to N+1

from imp import load_source
from os import path
from sys import argv

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
        "version": hachoir.__version__,
        "url": hachoir.WEBSITE,
        "download_url": hachoir.WEBSITE,
        "author": "Hachoir team (see AUTHORS file)",
        "description": "Package of Hachoir parsers used to open binary files",
        "long_description": long_description,
        "classifiers": CLASSIFIERS,
        "license": hachoir.LICENSE,
        "packages": ['hachoir'],
        "scripts": ["hachoir-metadata", "hachoir-subfile"],
    }
    if use_setuptools:
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

