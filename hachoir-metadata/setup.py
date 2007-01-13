#!/usr/bin/env python

try:
    from setuptools import setup
    with_setuptools = True
except ImportError:
    from distutils.core import setup
    with_setuptools = False

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
    import hachoir_metadata
    install_options = {
        "name": 'hachoir-metadata',
        "version": hachoir_metadata.__version__,
        "url": URL,
        "download_url": URL,
        "author": "Victor Stinner",
        "description": "Program to extract metadata using Hachoir library",
        "long_description": open('README').read(),
        "classifiers": CLASSIFIERS,
        "license": 'GNU GPL v2',
        "scripts": ["hachoir-metadata"],
        "packages": ["hachoir_metadata"],
        "package_dir": {"hachoir_metadata": "hachoir_metadata"},
    }
    if with_setuptools:
        install_options["install_requires"] = ["hachoir-core>=0.7.1", "hachoir-parser>=0.8.0"]
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

