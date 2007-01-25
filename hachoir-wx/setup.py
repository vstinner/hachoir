#!/usr/bin/env python
from imp import load_source
from os import path
from sys import argv
if "--setuptools" in argv:
    argv.remove("--setuptools")
    from setuptools import setup
    use_setuptools = True
else:
    from distutils.core import setup
    use_setuptools = False

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications',
    'Environment :: Win32 (MS Windows)',
    'Environment :: MacOS X',
    'Topic :: Software Development :: Disassemblers',
    'Topic :: Utilities',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Natural Language :: English',
    'Programming Language :: Python']

MODULES = ("field_view", "frame_view", "hex_view", "resource")

def main():
    hachoir_wx = load_source("version", path.join("hachoir_wx", "version.py"))

    PACKAGES = {"hachoir_wx": "hachoir_wx"}
    for name in MODULES:
        PACKAGES["hachoir_wx." + name] = path.join("hachoir_wx", name)

    install_options = {
        "name": hachoir_wx.PACKAGE,
        "version": hachoir_wx.VERSION,
        "url": hachoir_wx.WEBSITE,
        "download_url": hachoir_wx.WEBSITE,
        "license": hachoir_wx.LICENSE,
        "author": "Cyril Zorin",
        "description": "hachoir-wx is a wxWidgets GUI that's meant to provide a (more) user-friendly interface to the hachoir binary parsing engine",
        "long_description": open('README').read(),
        "classifiers": CLASSIFIERS,
        "scripts": ["hachoir-wx"],
        "packages": PACKAGES.keys(),
        "package_dir": PACKAGES,
        "package_data": {"hachoir_wx.resource": ['hachoir_wx.xrc']},
    }

    if use_setuptools:
        install_options["install_requires"] = (
            "hachoir-core>=0.7.0", "hachoir-parser>=0.7.0",
            "wxPython>=2.6.3")
        install_options["zip_safe"] = True
        install_options["include_package_data"] = True
    setup(**install_options)

if __name__ == "__main__":
    main()

