*******
Hachoir
*******

.. image:: https://travis-ci.org/haypo/hachoir3.svg?branch=master
   :alt: Build status of hachoir3 on Travis CI
   :target: https://travis-ci.org/haypo/hachoir3

Hachoir is a Python library to view and edit a binary stream field by field.
In other words, Hachoir allows you to "browse" any binary stream just like you
browse directories and files.

A file is splitted in a tree of fields, where the smallest field is just one
bit. Examples of fields types: integers, strings, bits, padding types, floats,
etc. Hachoir is the French word for a meat grinder (meat mincer), which is used
by butchers to divide meat into long tubes; Hachoir is used by computer
butchers to divide binary files into fields.

* `Hachoir3 website <http://hachoir3.readthedocs.io/>`_
* `Hachoir3 on GitHub (Source code, bug tracker) <https://github.com/haypo/hachoir3>`_
* License: GNU GPL v2

Hachoir3 is written for Python 3.3+, it uses the new ``yield from`` syntax.
For Python 2, see the `Hachoir project on Bitbucket
<https://bitbucket.org/haypo/hachoir>`_.