Welcome to Hachoir's documentation!
===================================

*Hachoir* is a Python library to view and edit a binary stream field by field.
In other words, Hachoir allows you to "browse" any binary stream just like you
browse directories and files. A file is splitted in a tree of fields, where the
smallest field is just one bit. Examples of fields types: integers,
strings, bits, padding types, floats, etc. Hachoir is the French word for a
meat grinder (meat mincer), which is used by butchers to divide meat into long
tubes; Hachoir is used by computer butchers to divide binary files into fields.

* `Hachoir3 website <http://hachoir3.readthedocs.io/>`_ (this site)
* `Hachoir3 at GitHub <https://github.com/haypo/hachoir3>`_ (source code, bugs)

Command line tools using Hachoir parsers:

* :ref:`hachoir-metadata <metadata>`: get metadata from binary files
* :ref:`hachoir-urwid <urwid>`: display the content of a binary file in text mode
* :ref:`hachoir-grep <grep>`: find a text pattern in a binary file
* :ref:`hachoir-strip <strip>`: modify a file to remove metadata

See also `Hachoir at Bitbucket <https://bitbucket.org/haypo/hachoir/>`_:
original Hachoir for Python 2.


User Guide
==========

.. toctree::
   :maxdepth: 1

   install
   metadata
   urwid
   subfile
   grep
   strip


Developer Guide
===============

.. toctree::
   :maxdepth: 1

   developer
   internals
   parser
   regex
   editor

Others pages
============

.. toctree::
   :maxdepth: 1

   contact
   hacking
   authors
   changelog
