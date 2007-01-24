#!/usr/bin/env python
from imp import load_source
from os import path
import sys

if "--setuptools" in sys.argv:
    sys.argv.remove("--setuptools")
    from setuptools import setup
    use_setuptools = True
else:
    from distutils.core import setup
    use_setuptools = False

URL = 'http://hachoir.org/wiki/hachoir-metadata'
CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'Topic :: Multimedia',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']

def main():
    hachoir_metadata = load_source("version", path.join("hachoir_metadata", "version.py"))
    install_options = {
        "name": hachoir_metadata.PACKAGE,
        "version": hachoir_metadata.VERSION,
        "url": hachoir_metadata.WEBSITE,
        "download_url": hachoir_metadata.WEBSITE,
        "author": "Victor Stinner",
        "description": "Program to extract metadata using Hachoir library",
        "long_description": open('README').read(),
        "classifiers": CLASSIFIERS,
        "license": hachoir_metadata.LICENCE,
        "scripts": ["hachoir-metadata"],
        "packages": ["hachoir_metadata"],
        "package_dir": {"hachoir_metadata": "hachoir_metadata"},
    }
    if use_setuptools:
        install_options["install_requires"] = ["hachoir-core>=0.7.2", "hachoir-parser>=0.8.1"]
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

