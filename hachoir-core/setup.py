#!/usr/bin/env python

# Procedure to release a new version:
#  - edit hachoir_core/version.py: VERSION = "XXX"
#  - edit ChangeLog (set release date)
#  - run: ./test_doc.py
#  - run: hg commit
#  - run: hg tag hachoir-core-XXX
#  - run: hg push
#  - run: python2.5 ./setup.py --setuptools register sdist bdist_egg upload
#  - run: python2.4 ./setup.py --setuptools bdist_egg upload
#  - run: python2.6 ./setup.py --setuptools bdist_egg upload
#  - check: http://pypi.python.org/pypi/hachoir-core
#  - update the website
#    * http://bitbucket.org/haypo/hachoir/wiki/Install/source
#    * http://bitbucket.org/haypo/hachoir/wiki/Home
#  - edit hachoir_core/version.py: set version to N+1
#  - edit ChangeLog: add a new "hachoir-core N+1" section with text XXX

# Constants
AUTHORS = 'Julien Muchembled, Victor Stinner'
DESCRIPTION = "Core of Hachoir framework: parse and edit binary files"
CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 5 - Production/Stable',
    'Environment :: Plugins',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']

import sys
from os.path import join as path_join
from imp import load_source

def main():
    # Check Python version!
    if sys.hexversion < 0x2040000:
        print "Sorry, you need Python 2.4 or greater to run (install) Hachoir!"
        sys.exit(1)

    if "--setuptools" in sys.argv:
        sys.argv.remove("--setuptools")
        from setuptools import setup
        use_setuptools = True
    else:
        from distutils.core import setup
        use_setuptools = False

    # Set some variables
    hachoir_core = load_source("version", path_join("hachoir_core", "version.py"))
    long_description = open('README').read() + open('ChangeLog').read()

    install_options = {
        "name": hachoir_core.PACKAGE,
        "version": hachoir_core.VERSION,
        "url": hachoir_core.WEBSITE,
        "download_url": hachoir_core.WEBSITE,
        "license": hachoir_core.LICENSE,
        "author": AUTHORS,
        "description": DESCRIPTION,
        "classifiers": CLASSIFIERS,
        "packages": ['hachoir_core', 'hachoir_core.field', 'hachoir_core.stream'],
        "long_description": long_description,
    }

    if use_setuptools:
        install_options["zip_safe"] = True

    # Call main() setup function
    setup(**install_options)

if __name__ == "__main__":
    main()

