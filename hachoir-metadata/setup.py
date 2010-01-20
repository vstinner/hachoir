#!/usr/bin/python

# Procedure to release a new version:
#  - edit hachoir_metadata/version.py: VERSION = "XXX"
#  - edit setup.py: install_options["install_requires"] = ["hachoir-core>=1.3", "hachoir-parser>=1.3"]
#  - edit ChangeLog (set release date)
#  - run: ./run_testcase.py ~/testcase
#  - hg commit
#  - hg tag hachoir-metadata-XXX
#  - hg push
#  - run: python2.5 ./setup.py --setuptools register sdist bdist_egg upload
#  - run: python2.4 ./setup.py --setuptools bdist_egg upload
#  - run: python2.6 ./setup.py --setuptools bdist_egg upload
#  - check http://pypi.python.org/pypi/hachoir-metadata
#  - update the web page:
#    http://bitbucket.org/haypo/hachoir/wiki/Install/source

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
    'Topic :: Multimedia',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']

def main():
    hachoir_metadata = load_source("version", path.join("hachoir_metadata", "version.py"))
    long_description = open('README').read() + open('ChangeLog').read()
    install_options = {
        "name": hachoir_metadata.PACKAGE,
        "version": hachoir_metadata.VERSION,
        "url": hachoir_metadata.WEBSITE,
        "download_url": hachoir_metadata.WEBSITE,
        "author": "Victor Stinner",
        "description": "Program to extract metadata using Hachoir library",
        "long_description": long_description,
        "classifiers": CLASSIFIERS,
        "license": hachoir_metadata.LICENSE,
        "scripts": ["hachoir-metadata", "hachoir-metadata-gtk"],
        "packages": ["hachoir_metadata"],
        "package_dir": {"hachoir_metadata": "hachoir_metadata"},
    }
    if use_setuptools:
        install_options["install_requires"] = ["hachoir-core>=1.3", "hachoir-parser>=1.3"]
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

