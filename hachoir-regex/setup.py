#!/usr/bin/env python

# Todo list to prepare a release:
#  - set version in hachoir_regex/version.py
#  - set release date in the README file
#  - create a Mercurial tag
#  - push the Mercurial
#  - ./setup.py register sdist bdist_egg upload
#  - update the website
#    * http://bitbucket.org/haypo/hachoir/wiki/Install/source
#    * http://bitbucket.org/haypo/hachoir/wiki/Home
#
# After the release:
#  - set version to n+1
#  - add a new empty section in the changelog for version n+1


# Constants
AUTHORS = 'Victor Stinner'
DESCRIPTION = "Manipulation of regular expressions (regex)"
CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: Software Development :: Interpreters',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Text Processing',
    'Topic :: Utilities',
]
PACKAGES = {"hachoir_regex": "hachoir_regex"}

from imp import load_source
from os import path
import sys

def main():
    if "--setuptools" in sys.argv:
        sys.argv.remove("--setuptools")
        from setuptools import setup
        use_setuptools = True
    else:
        from distutils.core import setup
        use_setuptools = False

    hachoir_regex = load_source("version", path.join("hachoir_regex", "version.py"))

    install_options = {
        "name": hachoir_regex.PACKAGE,
        "version": hachoir_regex.__version__,
        "url": hachoir_regex.WEBSITE,
        "download_url": hachoir_regex.WEBSITE,
        "license": hachoir_regex.LICENSE,
        "author": AUTHORS,
        "description": DESCRIPTION,
        "classifiers": CLASSIFIERS,
        "packages": PACKAGES.keys(),
        "package_dir": PACKAGES,
        "long_description": open('README').read(),
    }

    if use_setuptools:
        install_options["zip_safe"] = True

    # Call main() setup function
    setup(**install_options)

if __name__ == "__main__":
    main()

