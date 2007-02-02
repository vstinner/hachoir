#!/usr/bin/env python

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

import os
import sys
import hachoir_core

def getPackages(hachoir_dir):
    # TODO: Remove this ugly function to use __import__
    packages_dir = {
        'hachoir_core': [],
        'hachoir_core.field': ['field'],
        'hachoir_core.stream': ['stream'],
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
    root_dir = os.path.dirname(__file__)
    hachoir_dir = os.path.join(root_dir, "hachoir_core")
    long_description = get_long_description(root_dir)
    packages, package_dir = getPackages(hachoir_dir)

    install_options = {
        "name": hachoir_core.PACKAGE,
        "version": hachoir_core.__version__,
        "url": hachoir_core.WEBSITE,
        "download_url": hachoir_core.WEBSITE,
        "author": AUTHORS,
        "description": DESCRIPTION,
        "classifiers": CLASSIFIERS,
        "license": hachoir_core.LICENSE,
        "packages": packages,
        "package_dir": package_dir,
        "long_description": long_description,
    }

    if use_setuptools:
        install_options["zip_safe"] = True

    # Call main() setup function
    setup(**install_options)

if __name__ == "__main__":
    main()

