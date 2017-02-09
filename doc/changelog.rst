+++++++++
Changelog
+++++++++

hachoir 3.0a2
=============

* Python parser supports Python 3.3-3.7 .pyc files.
* metadata: get comment from ZIP
* Fix ResourceWarning warnings on files. Add a close() method and support for
  the context manager protocol ("with obj: ...") to parsers, input and output
  streams.

hachoir 3.0a1 (2017-01-09)
==========================

Changes:

* metadata: support TIFF picture

Big refactoring:

* First release of the Python 3 port
* The 7 Hachoir subprojects (core, editor, metadata, parser, regex, subfile,
  urwid) which lived in different directories are merged again into one big
  unique Python 3 module: hachoir. For example, "hachoir_parser" becomes
  "hachoir.parser".
* The project moved from Bitbucket (Mercurial repository) to GitHub (Git
  repository). The Mercurial history since 2007 was kept.
* Reorganize tests into a new tests/ subdirectory. Copy test files directly
  into the Git repository, instead of relying on an old FTP server which
  is not convenient. For example, it's now possible to add the required test
  file in a Git commit. So it's more convenient for pull requests as well.
* Port code to Python 3: "for field in parser: yield field" becomes
  "yield from parser".
* Fix PEP 8 issues: most of the code does now respect the latest PEP 8 coding
  style.
* Enable Travis CI on the project: tests are on Python 3.5, check also
  pep8 and documentation.
* Copy old wiki pages and documentation splitted into many subdirectories
  into a single consistent Sphinx documentation in the doc/ subdirectory.
  Publish the documentation online at http://hachoir3.readthedocs.io/
