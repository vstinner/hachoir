+++++++++++++++
Install Hachoir
+++++++++++++++

Packages
========

Mandriva
--------

To install Hachoir::

    urpmi python-hachoir-metadata

Packages:

* `python-hachoir-core 1.0.1 <http://sophie.zarb.org/rpm/,i586/python-hachoir-core>`_
* `python-hachoir-parser 1.0 <http://sophie.zarb.org/rpm/,i586/python-hachoir-parser>`_
* `python-hachoir-metadata 1.0 <http://sophie.zarb.org/rpm/,i586/python-hachoir-metadata>`_
* `python-hachoir-urwid 1.0.1 <http://sophie.zarb.org/rpm/,i586/python-hachoir-urwid>`_
* `python-hachoir-regex 1.0.2 <http://sophie.zarb.org/rpm/,i586/python-hachoir-regex>`_
* `python-hachoir-subfile 0.5.2 <http://sophie.zarb.org/rpm/,i586/python-hachoir-subfile>`_

Gentoo
------

Hachoir is part of Gentoo since the 2007-07-14.

Portage details:

* `hachoir-core 1.0.1 <http://gentoo-portage.com/dev-python/hachoir-core>`_
* `hachoir-parser 1.0 <http://gentoo-portage.com/dev-python/hachoir-parser>`_
* `hachoir-metadata 1.0 <http://gentoo-portage.com/app-misc/hachoir-metadata>`_
* `hachoir-subfile 0.5.2 <http://gentoo-portage.com/app-misc/hachoir-subfile>`_
* `hachoir-urwid 1.0.1 <http://gentoo-portage.com/app-misc/hachoir-urwid>`_
* `hachoir-regex 1.0.2 <http://gentoo-portage.com/dev-python/hachoir-regex>`_

Arch
----

arno's packages (on bursab.free.fr):

* `hachoir-core 1.0.1 <http://aur.archlinux.org/packages.php?do_Details=1&ID=12016>`_
* `hachoir-parser 1.0 <http://aur.archlinux.org/packages.php?do_Details=1&ID=12017>`_
* `hachoir-metadata 1.0.1 <http://aur.archlinux.org/packages.php?do_Details=1&ID=12018>`_
* `hachoir-urwid 1.0 <http://aur.archlinux.org/packages.php?do_Details=1&ID=12022>`_
* `hachoir-regex 1.0.2 <http://aur.archlinux.org/packages.php?do_Details=1&ID=12020>`_
* `hachoir-subfile 0.5.1 <http://aur.archlinux.org/packages.php?do_Details=1&ID=12021>`_


Debian
------

Hachoir is part of Debian project since 2007-04-22, so just type::

    sudo apt-get install python-hachoir-metadata
    sudo apt-get install python-hachoir-urwid
    sudo apt-get install python-hachoir-wx

Packages information:

* `python-hachoir-core <http://packages.debian.org/unstable/python/python-hachoir-core>`_
* `python-hachoir-parser <http://packages.debian.org/unstable/python/python-hachoir-parser>`_
* `python-hachoir-regex <http://packages.debian.org/unstable/python/python-hachoir-regex>`_
* `python-hachoir-metadata <http://packages.debian.org/unstable/python/python-hachoir-metadata>`_
* `python-hachoir-urwid <http://packages.debian.org/unstable/python/python-hachoir-urwid>`_
* `python-hachoir-wx <http://packages.debian.org/unstable/python/python-hachoir-wx>`_
* `python-hachoir-subfile <http://packages.debian.org/unstable/python/python-hachoir-subfile>`_

Latest version (hachoir-core 1.1 and companions) entered unstable (sid) on
2008-04-25.  The packages can be installed on etch as they are built and tested
under this release. They aren't usable under sarge (oldstable).


Stable version (tarballs)
=========================

Download tarballs
-----------------

* `hachoir-core-1.3.3.tar.gz <http://cheeseshop.python.org/packages/source/h/hachoir-core/hachoir-core-1.3.3.tar.gz>`_
* `hachoir-parser-1.3.4.tar.gz <http://cheeseshop.python.org/packages/source/h/hachoir-parser/hachoir-parser-1.3.4.tar.gz>`_
* `hachoir-metadata-1.3.3.tar.gz <http://cheeseshop.python.org/packages/source/h/hachoir-metadata/hachoir-metadata-1.3.3.tar.gz>`_
* `hachoir-urwid-1.1.tar.gz <http://cheeseshop.python.org/packages/source/h/hachoir-urwid/hachoir-urwid-1.1.tar.gz>`_
* `hachoir-wx-0.3.tar.gz <http://cheeseshop.python.org/packages/source/h/hachoir-wx/hachoir-wx-0.3.tar.gz>`_
* `hachoir-subfile-0.5.3.tar.gz <http://cheeseshop.python.org/packages/source/h/hachoir-subfile/hachoir-subfile-0.5.3.tar.gz>`_
* `hachoir-regex-1.0.5.tar.gz <http://cheeseshop.python.org/packages/source/h/hachoir-regex/hachoir-regex-1.0.5.tar.gz>`_

PyPI entries
------------

* `hachoir-core on the Python Cheeseshop (PyPI)
  <http://cheeseshop.python.org/pypi/hachoir-core>`_
* `hachoir-metadata on the Python Cheeseshop (PyPI)
  <http://cheeseshop.python.org/pypi/hachoir-metadata>`_

Dependencies
------------

* hachoir-regex 1.0

 -  (nothing)

* hachoir-core 1.3.3

 -  (nothing)

* hachoir-parser 1.3.3

 -  hachoir-core 1.3

* hachoir-metadata 1.3.2

 -  hachoir-core 1.3
 -  hachoir-parser 1.3
 -  optional: profiler module of Python

* hachoir-urwid 1.1

 -  hachoir-core 1.2
 -  hachoir-parser 1.0
 -  `urwid <http://excess.org/urwid/>`_ 0.9.4
 -  optional: profiler module of Python

* hachoir-wx 0.3

 -  hachoir-core 1.2
 -  hachoir-parser 0.7
 -  `wxPython <http://www.wxpython.org/>`_ with Unicode support (2.6.3+ or 2.7.2+)

* hachoir-subfile 0.5.3

 -  hachoir-core 1.1
 -  hachoir-parser 1.1
 -  hachoir-regex 1.0.5
 -  optional: profiler module of Python


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

    DIR=$HOME/hachoir
    ./setup.py install --install-script=$DIR --install-purelib=$DIR


Developer version (Mercurial)
=============================

The latest version of Hachoir is always in Mercurial. Instruction to install
Hachoir using Mercurial is similar to an installation from source code. But
instead of downloading tarballs, use::

    hg clone http://bitbucket.org/haypo/hachoir/

Use "source setupenv.sh" to setup the PYTHONPATH environment variable (to use
Hachoir without installation).

Windows user, use `TortoiseHg <http://tortoisehg.bitbucket.org/>`_ to download
the Mercurial source code.


Statistics about source code
============================

See `ohloh.net reports <http://next.ohloh.net/projects/3183>`_.

