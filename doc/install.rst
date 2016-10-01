+++++++
Install
+++++++

Dependencies
------------

GnomeKeyring parser requires Python Crypto module:
http://www.amk.ca/python/code/crypto.html

hachoir-urwid:

* urwid

hachoir-metadata-gtk:

* python3-gobject

hachoir-metadata-qt:

* PyQt4
* To compile hachoir_metadata/qt/dialog.ui, you need pyuic4 which is part of
  PyQt4 development tools.

* hachoir-urwid

 -  `urwid <http://excess.org/urwid/>`_ 0.9.4
 -  optional: profiler module of Python

* hachoir-wx

 -  `wxPython <http://www.wxpython.org/>`_ with Unicode support (2.6.3+ or 2.7.2+)


Notes for Windows user (urwid)
------------------------------

If you want to use [[hachoir-urwid|hachoir-urwid]] program, follow these instructions.

hachoir-urwid requires urwid library, but urwid requires //curses// Python module but also small patches for urwid:

 * `Patch from Gottfried Ganßauge <http://www.mail-archive.com/urwid%40lists.excess.org/msg00010.html>`_
 * `wcurses <http://adamv.com/dev/python/curses/>`_ (curses of //AdamV//), for
   Python 2.5, download `curses-python2.5-win32
   <http://hachoir.org/attachment/wiki/hachoir-urwid/curses-python2.5-win32.zip?format=raw>`_
   => decompress curses/ directory in Hachoir directory

Another version of curses: `PDCurses <http://pdcurses.sourceforge.net/>`_ (//Public Domain Curses//).


Uncompress and run setup.py
---------------------------

* Uncompress each tarball, eg. ``tar -xvzf hachoir-metadata-0.8.1.tar.gz``
* Go to Hachoir directory, eg. ``cd hachoir-metadata-0.8.1``
* (with administrator privileges) Run setup.py: ```python setup.py install``


Install without administrator privileges
----------------------------------------

If you don't have administrator privileges, you install Hachoir in your home.
Use same instruction than above but instead of running setup.py directory,
use::

    python3 setup.py install --user


Developer version (Git)
=======================

The latest version of Hachoir is always in Git. Instruction to install
Hachoir using Git is similar to an installation from source code. But
instead of downloading tarballs, use::

    git clone https://github.com/haypo/hachoir3
