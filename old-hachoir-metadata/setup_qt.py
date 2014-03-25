#!/usr/bin/env python3
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
    PACKAGES = ["hachoir.metadata"]

    from subprocess import call
    SCRIPTS.append("hachoir-metadata-qt")
    dialog = "hachoir.metadata/qt/dialog"
    dialog_python = dialog + "_ui.py"
    command = ["pyuic4", "-o", dialog_python, dialog + ".ui"]
    try:
        exitcode = call(command)
    except OSError as err:
        exitcode = 1
    if exitcode:
        if path.exists(dialog_python):
            print("Warning: unable to recompile dialog.ui to dialog_ui.py using pyuic4", file=sys.stderr)
            print('(use command "%s --disable-qt" to disable this warning)' % ' '.join(sys.argv), file=sys.stderr)
            print(file=sys.stderr)
        else:
            print("ERROR: Unable to compile dialog.ui to dialog_ui.py using pyuic4", file=sys.stderr)
            print('Use command "%s --disable-qt" to skip hachoir-metadata-qt' % ' '.join(sys.argv), file=sys.stderr)
            print('pyuic4 is included in the PyQt4 development package', file=sys.stderr)
            sys.exit(1)
    PACKAGES.append("hachoir.metadata.qt")

    hachoir.metadata = load_source("version", path.join("hachoir.metadata", "version.py"))
    long_description = open('README').read() + open('ChangeLog').read()
    install_options = {
        "name": hachoir.metadata.PACKAGE,
        "version": hachoir.metadata.VERSION,
        "url": hachoir.metadata.WEBSITE,
        "download_url": hachoir.metadata.WEBSITE,
        "author": "Victor Stinner",
        "description": "Program to extract metadata using Hachoir library",
        "long_description": long_description,
        "classifiers": CLASSIFIERS,
        "license": hachoir.metadata.LICENSE,
        "scripts": SCRIPTS,
        "packages": PACKAGES,
    }
    if use_setuptools:
        install_options["install_requires"] = ["hachoir-core>=1.3", "hachoir-parser>=1.3"]
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

