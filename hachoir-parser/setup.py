#!/usr/bin/env python
from imp import load_source
from os import path
from sys import argv
from README import writeReadme
from StringIO import StringIO

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']
MODULES = (
    "archive", "audio", "container", "common", "file_system", "game",
    "image", "misc", "network", "program", "video")

def getLongDescription():
    out = StringIO()
    writeReadme(out)
    out.seek(0)
    return out.read()

def main():
    if "--setuptools" in argv:
        argv.remove("--setuptools")
        from setuptools import setup
        use_setuptools = True
    else:
        from distutils.core import setup
        use_setuptools = False


    hachoir_parser = load_source("version", path.join("hachoir_parser", "version.py"))
    PACKAGES = {"hachoir_parser": "hachoir_parser"}
    for name in MODULES:
        PACKAGES["hachoir_parser." + name] = "hachoir_parser/" + name

    install_options = {
        "name": hachoir_parser.PACKAGE,
        "version": hachoir_parser.__version__,
        "url": hachoir_parser.WEBSITE,
        "download_url": hachoir_parser.WEBSITE,
        "author": "Hachoir team (see AUTHORS file)",
        "description": "Package of Hachoir parsers used to open binary files",
        "long_description": getLongDescription(),
        "classifiers": CLASSIFIERS,
        "license": hachoir_parser.LICENSE,
        "packages": PACKAGES.keys(),
        "package_dir": PACKAGES,
    }
    if use_setuptools:
        install_options["install_requires"] = "hachoir-core>=1.2.1"
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

