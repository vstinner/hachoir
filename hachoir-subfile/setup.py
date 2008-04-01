#!/usr/bin/env python

# Constants
AUTHORS = 'Victor Stinner'
DESCRIPTION = "Find subfile in any binary stream"
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: Software Development :: Disassemblers',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System :: Filesystems',
    'Topic :: Utilities',
]
PACKAGES = {"hachoir_subfile": "hachoir_subfile"}

from imp import load_source
from os import path
import sys

def main():
    # Check Python version!
    if sys.hexversion < 0x2040000:
        print "Sorry, you need Python 2.4 or greater to run (install) hachoir-subfile!"
        sys.exit(1)

    if "--setuptools" in sys.argv:
        sys.argv.remove("--setuptools")
        from setuptools import setup
        use_setuptools = True
    else:
        from distutils.core import setup
        use_setuptools = False

    hachoir_subfile = load_source("version", path.join("hachoir_subfile", "version.py"))

    install_options = {
        "name": hachoir_subfile.PACKAGE,
        "version": hachoir_subfile.VERSION,
        "url": hachoir_subfile.WEBSITE,
        "download_url": hachoir_subfile.WEBSITE,
        "license": hachoir_subfile.LICENSE,
        "author": AUTHORS,
        "description": DESCRIPTION,
        "classifiers": CLASSIFIERS,
        "packages": PACKAGES.keys(),
        "package_dir": PACKAGES,
        "long_description": open('README').read(),
        "scripts": ["hachoir-subfile"],
    }

    if use_setuptools:
        install_options["zip_safe"] = True
        install_options["install_requires"] = (
            "hachoir-core>=1.1",
            "hachoir-parser>=1.1",
            "hachoir-regex>=1.0.1")

    # Call main() setup function
    setup(**install_options)

if __name__ == "__main__":
    main()

