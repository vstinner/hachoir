#!/usr/bin/python

# Script to install hachoir-metadata module and programs
#
# Options:
#   --setuptools: use setuptools instead of distutils
#   --disable-qt: don't install hachoir-metadata-qt
#
#---------------
#
# Procedure to release a new version:
#  - edit hachoir_metadata/version.py: VERSION = "XXX"
#  - edit setup.py: install_options["install_requires"] = ["hachoir-core>=1.3", "hachoir-parser>=1.3"]
#  - edit INSTALL: Dependencies section
#  - edit ChangeLog (set release date)
#  - run: ./test_doc.py
#  - run: ./run_testcase.py ~/testcase
#  - run: hg commit
#  - run: hg tag hachoir-metadata-XXX
#  - run: hg push
#  - run: python2.5 ./setup.py --setuptools register sdist bdist_egg upload
#  - run: python2.4 ./setup.py --setuptools bdist_egg upload
#  - run: python2.6 ./setup.py --setuptools bdist_egg upload
#  - check: http://pypi.python.org/pypi/hachoir-metadata
#  - update the website
#    * http://bitbucket.org/haypo/hachoir/wiki/Install/source
#    * http://bitbucket.org/haypo/hachoir/wiki/Home
#  - edit hachoir_metadata/version.py: set version to N+1 in
#  - edit ChangeLog: add a new "hachoir-metadata N+1" section with text XXX

from imp import load_source
from os import path
import sys

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
    if "--setuptools" in sys.argv:
        sys.argv.remove("--setuptools")
        from setuptools import setup
        use_setuptools = True
    else:
        from distutils.core import setup
        use_setuptools = False

    SCRIPTS = ["hachoir-metadata", "hachoir-metadata-gtk"]
    PACKAGES = ["hachoir_metadata"]

    if "--disable-qt" not in sys.argv:
        from subprocess import call
        SCRIPTS.append("hachoir-metadata-qt")
        dialog = "hachoir_metadata/qt/dialog"
        dialog_python = dialog + "_ui.py"
        command = ["pyuic4", "-o", dialog_python, dialog + ".ui"]
        try:
            exitcode = call(command)
        except OSError, err:
            exitcode = 1
        if exitcode:
            if path.exists(dialog_python):
                print >>sys.stderr, "Warning: unable to recompile dialog.ui to dialog_ui.py using pyuic4"
                print >>sys.stderr, '(use command "%s --disable-qt" to disable this warning)' % ' '.join(sys.argv)
                print >>sys.stderr
            else:
                print >>sys.stderr, "ERROR: Unable to compile dialog.ui to dialog_ui.py using pyuic4"
                print >>sys.stderr, 'Use command "%s --disable-qt" to skip hachoir-metadata-qt' % ' '.join(sys.argv)
                print >>sys.stderr, 'pyuic4 is included in the PyQt4 development package'
                sys.exit(1)
        PACKAGES.append("hachoir_metadata.qt")
    else:
        sys.argv.remove("--disable-qt")

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
        "scripts": SCRIPTS,
        "packages": PACKAGES,
    }
    if use_setuptools:
        install_options["install_requires"] = ["hachoir-core>=1.3", "hachoir-parser>=1.3"]
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

