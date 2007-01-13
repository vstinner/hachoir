#!/usr/bin/env python

try:
    from setuptools import setup
    with_setuptools = True
except ImportError:
    from distutils.core import setup
    with_setuptools = False

URL = 'http://hachoir.org/wiki/hachoir-wx'
CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console :: Curses',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']

def main():
    import hachoir_wx
    install_options = {
        "name": 'hachoir-wx',
        "version": hachoir_wx.__version__,
        "url": URL,
        "download_url": URL,
        "author": "Julien Muchembled and Victor Stinner",
        "description": "hachoir-wx is a wxWidgets GUI that's meant to provide a (more) user-friendly interface to the hachoir binary parsing engine",
        "long_description": open('README').read(),
        "classifiers": CLASSIFIERS,
        "license": 'GNU GPL v2',
        "scripts": ["hachoir-wx"],
        "packages": ["hachoir_wx"],
        "package_dir": {"hachoir_wx": "hachoir_wx"},
    }
    if with_setuptools:
        install_options["install_requires"] = (
            "hachoir-core>=0.7.0", "hachoir-parser>=0.7.0",
            "wxPython>=2.6.3")
        install_options["zip_safe"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

