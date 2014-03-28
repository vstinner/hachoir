Welcome to Hachoir's documentation!
===================================

Hachoir is the French name for a mincer: a tool used by butchers to cut meat.
Hachoir is also a tool written for hackers to cut a file or any binary stream.
A file is split in a tree of fields where the smallest field can be a
bit. There are various field types: integer, string, bits, padding, sub file,
etc.

Hachoir is the french name for a mincer: a tool used by butchers to cut meat.
Hachoir is also a tool written for hackers to cut file or any binary stream. A
file is splitted in a tree of fields where the smallest field can be just a
bit. There are various field types: integer, string, bits, padding, sub file,
etc.

Hachoir is a Python library used to represent of a binary file as a tree of
Python objects. Each object has a type, a value, an address, etc. The goal is
to be able to know the meaning of each bit in a file.


Contents:

.. toctree::
   :maxdepth: 2

   home
   core
   parser
   metadata
   install
   regex
   metadata_examples
   api
   internals
   regex_api
   editor
   subfile
   grep
   strip
   authors
   changelog



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

