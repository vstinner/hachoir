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

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']

def main():
    hachoir_urwid = load_source("version", path.join("hachoir_urwid", "version.py"))
    install_options = {
        "name": hachoir_urwid.PACKAGE,
        "version": hachoir_urwid.VERSION,
        "url": hachoir_urwid.WEBSITE,
        "download_url": hachoir_urwid.WEBSITE,
        "license": hachoir_urwid.LICENSE,
        "author": "Julien Muchembled and Victor Stinner",
        "description": "Binary file explorer using Hachoir and urwid libraries",
        "long_description": open('README').read(),
        "classifiers": CLASSIFIERS,
        "scripts": ["hachoir-urwid"],
        "packages": ["hachoir_urwid"],
        "package_dir": {"hachoir_urwid": "hachoir_urwid"},
    }
    if use_setuptools:
        install_options["install_requires"] = (
            "hachoir-core>=1.2",
            "hachoir-parser>=1.0",
            "urwid>=0.9.4")
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

