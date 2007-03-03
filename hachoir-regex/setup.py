#!/usr/bin/env python

# Constants
AUTHORS = 'Victor Stinner'
DESCRIPTION = "Manipulation of regular expressions (regex)"
CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
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
import os
import sys

def getPackages(hachoir_dir):
    # TODO: Remove this ugly function to use __import__
    packages_dir = {
        'hachoir_regex': [],
    }
    old_packages_dir = packages_dir
    packages_dir = {}
    for key in old_packages_dir.iterkeys():
        packages_dir[key] = os.path.join(hachoir_dir, *old_packages_dir[key])
    return packages_dir.keys(), packages_dir

def get_long_description(root_dir):
    """Read the content of README file"""
    return open(os.path.join(root_dir, 'README'), 'r').read()

def main():
    # Check Python version!
    if sys.hexversion < 0x2040000:
        print "Sorry, you need Python 2.4 or greater to run (install) Hachoir regex!"
        sys.exit(1)

    if "--setuptools" in sys.argv:
        sys.argv.remove("--setuptools")
        from setuptools import setup
        use_setuptools = True
    else:
        from distutils.core import setup
        use_setuptools = False

    hachoir_parser = load_source("version", path.join("hachoir_regex", "version.py"))

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

