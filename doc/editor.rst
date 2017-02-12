.. _editor:

+++++++++++++++++++++
hachoir.editor module
+++++++++++++++++++++

Hachoir editor is a Python library based on Hachoir core used to edit binary
files.

Today, only one program uses it: :ref:`hachoir-strip <strip>` (remove "useless"
information to make a file smaller).

Example: gzip, remove filename
==============================

.. literalinclude:: examples/editor_gzip.py

Example: gzip, add extra
========================

.. literalinclude:: examples/editor_add_extra.py

Example: zip, set comment
=========================

.. literalinclude:: examples/editor_zip.py
