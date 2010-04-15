#!/usr/bin/env python
from imp import load_source
from os import path
from sys import argv

# Procedure to release a new version:
#  - edit hachoir_parser/version.py: __version__ = "XXX"
#  - edit setup.py: install_options["install_requires"] = "hachoir-core>=XXX"
#  - edit INSTALL: update Dependencies
#  - run: ./tests/run_testcase.py ~/testcase
#  - edit ChangeLog (set release date)
#  - run: hg commit
#  - run: hg tag hachoir-parser-XXX
#  - run: hg push
#  - run: ./README.py
#  - run: python2.5 ./setup.py --setuptools register sdist bdist_egg upload
#  - run: python2.4 ./setup.py --setuptools bdist_egg upload
#  - run: python2.6 ./setup.py --setuptools bdist_egg upload
#  - run: rm README
#  - check http://pypi.python.org/pypi/hachoir-parser
#  - update the website
#    * http://bitbucket.org/haypo/hachoir/wiki/Install/source
#    * http://bitbucket.org/haypo/hachoir/wiki/Home
#  - edit hachoir_parser/version.py: set version to N+1
#  - edit ChangeLog: add a new "hachoir-parser N+1" section with text XXX

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

    readme = open('README')
    long_description = readme.read()
    readme.close()

    install_options = {
        "name": hachoir_parser.PACKAGE,
        "version": hachoir_parser.__version__,
        "url": hachoir_parser.WEBSITE,
        "download_url": hachoir_parser.WEBSITE,
        "author": "Hachoir team (see AUTHORS file)",
        "description": "Package of Hachoir parsers used to open binary files",
        "long_description": long_description,
        "classifiers": CLASSIFIERS,
        "license": hachoir_parser.LICENSE,
        "packages": PACKAGES.keys(),
        "package_dir": PACKAGES,
    }
    if use_setuptools:
        install_options["install_requires"] = "hachoir-core>=1.3"
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

