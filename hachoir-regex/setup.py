#!/usr/bin/env python

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

