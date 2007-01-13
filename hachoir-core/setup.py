#!/usr/bin/env python

# Constants
AUTHORS = 'Julien Muchembled, Victor Stinner'
DOWNLOAD_URL = 'http://hachoir.org/wiki/hachoir-core'
DESCRIPTION = "Core of Hachoir framework: parse and edit binary files"
LICENSE = 'GNU GPL v2'
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

# setup.py commands specific to setuptools library
SETUPTOOLS_COMMANDS = ("rotate", "develop", "setopt",
    "saveopts", "egg_info", "upload", "install_egg_info", "alias",
    "easy_install", "bdist_egg", "test")

import os
import sys

# Import Hachoir
try:
    import hachoir_core
except ImportError:
    print "WTF? Where is Hachoir?"
    sys.exit(1)

def getPackages(hachoir_dir):
    # TODO: Remove this ugly function to use __import__
    packages_dir = {
        'hachoir_core': [],
        'hachoir_core.field': ['field'],
        'hachoir_core.stream': ['stream'],
        'hachoir_core.editor': ['editor'],
    }
    old_packages_dir = packages_dir
    packages_dir = {}
    for key in old_packages_dir.iterkeys():
        packages_dir[key] = os.path.join(hachoir_dir, *old_packages_dir[key])
    return packages_dir.keys(), packages_dir

def get_long_description(root_dir):
    """Read the content of README file"""
    return open(os.path.join(root_dir, 'README'), 'r').read()

def errorSetuptoolsNeeded(command):
    print """Error: You need setuptools Python package for the command "%s"!

Last version can be found at:
   http://peak.telecommunity.com/dist/ez_setup.py
(Hachoir has a backup copy, check setup.py directory)

To install it, type as root:
   python ez_setup.py""" % command

def errorMSINeeded():
    print """Error: You need bdist_msi extension to build MSI Windows package.
Download it at:
   http://www.dcl.hpi.uni-potsdam.de/home/loewis/bdist_msi/"""

def main():
    # Check Python version!
    if sys.hexversion < 0x2040000:
        print "Sorry, you need Python 2.4 or greater to run (install) Hachoir!"
        sys.exit(1)

    # Try to import setuptools (or use distutils fallback)
    with_setuptools = True
    try:
        from setuptools import setup
    except ImportError:
        # Is setuptools really needed?
        for arg in sys.argv[1:]:
            if arg in SETUPTOOLS_COMMANDS:
                errorSetuptoolsNeeded(arg)
                sys.exit(1)
        with_setuptools = False

        # Or use distutils
        from distutils.core import setup

    # Set some variables
    root_dir = os.path.dirname(__file__)
    hachoir_dir = os.path.join(root_dir, "hachoir_core")
    long_description = get_long_description(root_dir)
    packages, package_dir = getPackages(hachoir_dir)

    install_options = {
        "name": 'hachoir-core',
        "version": hachoir_core.__version__,
        "url": hachoir_core.WEBSITE,
        "download_url": DOWNLOAD_URL,
        "author": AUTHORS,
        "description": DESCRIPTION,
        "classifiers": CLASSIFIERS,
        "license": LICENSE,
        "packages": packages,
        "package_dir": package_dir,
        "long_description": long_description,
    }

    if with_setuptools:
        # Use MSI extension (to build clean Windows package)
        cmdclass = {}
        try:
            import bdist_msi
            cmdclass['bdist_msi'] = bdist_msi.bdist_msi
        except ImportError:
            for arg in sys.argv[1:]:
                if "msi" in arg:
                    errorMSINeeded()
                    sys.exit(1)

        install_options["zip_safe"] = True
        install_options["cmdclass"] = cmdclass

    # Call main() setup function
    setup(**install_options)

if __name__ == "__main__":
    main()

