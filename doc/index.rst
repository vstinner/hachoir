Welcome to Hachoir's documentation!
===================================

*Hachoir* is a Python library to view and edit a binary stream field by field.
In other words, Hachoir allows you to "browse" any binary stream just like you
browse directories and files. A file is splitted in a tree of fields, where the
smallest field is just one bit. Examples of fields types: integers,
strings, bits, padding types, floats, etc. Hachoir is the French word for a
meat grinder (meat mincer), which is used by butchers to divide meat into long
tubes; Hachoir is used by computer butchers to divide binary files into fields.

* `Hachoir3 website <http://hachoir3.readthedocs.org/>`_ (this site)
* `Hachoir3 at Bitbucket <https://bitbucket.org/haypo/hachoir3>`_

See also `Hachoir at Bitbucket <http://hachoir3.readthedocs.org/>`_: original
Hachoir for Python 2.


Table Of Contents
=================

.. toctree::
   :maxdepth: 2

   core
   parser
   metadata
   install
   urwid
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

Pages:

* [[Ideas|Ideas]] of projects based on Hachoir
* [[Developer|Developer section]]
* [[Contact|Contact]]
* [[Links|Links]]: Links to similar projects and news on other websites about Hachoir
* [[LegalIssue|Legal issues]]
* [[Forensics|Forensics]]
* [[FileFormatResources|File format resources]]
* [[MicrosoftOffice|Microsoft Office file formats]]
* [[hachoir-metadata|hachoir-metadata]]: extract metadata from video, music and other files
* [[hachoir-urwid|hachoir-urwid]]: text user interface
* [[hachoir-wx|hachoir-wx]]: graphical user interface (wxWidgets)
* [[hachoir-http|hachoir-http]]: HTML + Ajax user interface
* [[hachoir-gtk|hachoir-gtk]]: graphical (Gtk+) user interface
* [[Status|status of the project]].


News
====

* 2010-07-26: Release of hachoir-parser 1.3.4 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-parser/ChangeLog>`_) and hachoir-metadata 1.3.3 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-metadata/ChangeLog>`_)
* 2010-02-26: Release of hachoir-core 1.3.3 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-core/ChangeLog>`_)
* 2010-02-04: Release of hachoir-metdata 1.3.2 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-metadata/ChangeLog>`_)
* 2010-01-20: Release of hachoir-core 1.3 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-core/ChangeLog>`_), hachoir-parser 1.3 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-parser/ChangeLog>`_) and hachoir-metdata 1.3 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-metadata/ChangeLog>`_)
* 2010-01-13: Release of hachoir-regex 1.0.4 (`changes <http://bitbucket.org/haypo/hachoir/src/tip/hachoir-regex/README>`_)
* 2009-08-05: The website moved to a new server (bitbucket), the source code is now stored in a Mercurial repository instead of a Subversion repository
* October 2008: Release of hachoir-core 1.2.1 ([[browser:trunk/hachoir-core/ChangeLog|ChangeLog]]), hachoir-parser 1.2.1 ([[browser:trunk/hachoir-parser/ChangeLog|ChangeLog]]), hachoir-metadata 1.2.1 ([[browser:trunk/hachoir-metadata/ChangeLog|ChangeLog]])
* September 2008: Release of hachoir-core 1.2, hachoir-parser 1.2, hachoir-metadata 1.2, hachoir-wx 0.3, hachoir-urwid 1.1
* May 2008: Creation of `project FileSull <http://sourceforge.net/projects/filesull/>`_, fuzzer based on `Sulley <http://code.google.com/p/sulley/>`_ and Hachoir
* 1st April 2008

 -  Release of hachoir-core 1.1, hachoir-parser 1.1, hachoir-metadata 1.1, hachoir-subfile 0.5.3, hachoir-wx 0.2, hachoir-regex 1.0.3
 -  Changes:
 -  Create hachoir-metadata-gtk (basic Gtk+ GUI for hachoir-metadata)
 -  Create "EFI Platform Initialization Firmware Volume" (PIFV) and "Microsoft Windows Help" (HLP) parsers
 -  Metadata extractors are more stable and fault tolerant
 -  String value is always Unicode (guess charset if needed); many bugfixes and minor improvments

* 24 August 2007

 -  Server migration: Julien's server (81.56.123.123) to haypo's server (88.160.66.91). So ask haypo if you would like an account.

* 25 July 2007

 -  Most hachoir components are now available in version 1.0 for Debian, Mandriva, Gentoo, Arch and FreeBSD!

* ([[OldNews|read old news]])

