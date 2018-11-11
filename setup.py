#!/usr/bin/env python3
#
# Prepare a release:
#
#  - check version: hachoir/version.py and doc/conf.py
#  - set the release date: edit doc/changelog.rst
#  - run: git commit -a
#  - Remove untracked files/dirs: git clean -fdx
#  - run tests: tox
#  - run: git push
#  - check Travis CI status:
#    https://travis-ci.org/vstinner/hachoir
#
# Release a new version:
#
#  - run: git tag x.y.z
#  - run: git push --tags
#  - Remove untracked files/dirs: git clean -fdx
#  - run: python3 setup.py sdist bdist_wheel
#  - twine upload dist/*
#
# After the release:
#
#  - set version to N+1: hachoir/version.py and doc/conf.py

from imp import load_source
from os import path
from setuptools import find_packages

ENTRY_POINTS = {
    'console_scripts': [
        "hachoir-grep = hachoir.grep:main",
        "hachoir-metadata = hachoir.metadata.main:main",
        "hachoir-strip = hachoir.strip:main",
        "hachoir-urwid = hachoir.urwid_ui:main"
    ],
    'gui_scripts': [
        "hachoir-wx = hachoir.wx.main:main"
    ]
}
# FIXME: hachoir-subfile is currently broken
# "hachoir-subfile",

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'Environment :: Plugins',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3',
    'Topic :: Multimedia',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: Software Development :: Disassemblers',
    'Topic :: Software Development :: Interpreters',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: System :: Filesystems',
    'Topic :: Text Processing',
    'Topic :: Utilities',
]


def main():
    from setuptools import setup

    hachoir = load_source("version", path.join("hachoir", "version.py"))

    readme = open('README.rst')
    long_description = readme.read()
    readme.close()

    install_options = {
        "name": hachoir.PACKAGE,
        "version": hachoir.VERSION,
        "url": hachoir.WEBSITE,
        "author": "Hachoir team (see AUTHORS file)",
        "description": "Package of Hachoir parsers used to open binary files",
        "long_description": long_description,
        "classifiers": CLASSIFIERS,
        "license": hachoir.LICENSE,
        "packages": find_packages(),
        "package_data": {"hachoir.wx.resource": ['hachoir_wx.xrc']},
        "entry_points": ENTRY_POINTS,
        "extras_require": {
            "urwid": [
                "urwid==1.3.1"
            ]
        },
        "zip_safe": True,
    }
    setup(**install_options)


if __name__ == "__main__":
    main()
