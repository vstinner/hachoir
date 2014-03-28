+++++++++
Changelog
+++++++++

Hachoir Core
^^^^^^^^^^^^

hachoir-core 1.3.4
==================

 * Fix bin2long() on Python 2.7

hachoir-core 1.3.3 (2010-02-26)
===============================

 * Add writelines() method to UnicodeStdout

hachoir-core 1.3.2 (2010-01-28)
===============================

 * MANIFEST.in includes also the documentation

hachoir-core 1.3.1 (2010-01-21)
===============================

 * Create MANIFEST.in to include ChangeLog and other files for setup.py

hachoir-core 1.3 (2010-01-20)
=============================

 * Add more charsets to GenericString: CP874, WINDOWS-1250, WINDOWS-1251,
   WINDOWS-1254, WINDOWS-1255, WINDOWS-1256,WINDOWS-1257, WINDOWS-1258,
   ISO-8859-16
 * Fix initLocale(): return charset even if config.unicode_stdout is False
 * initLocale() leave sys.stdout and sys.stderr unchanged if the readline
   module is loaded: Hachoir can now be used correctly with ipython
 * HachoirError: replace "message" attribute by "text" to fix Python 2.6
   compatibility (message attribute is deprecated)
 * StaticFieldSet: fix Python 2.6 warning, object.__new__() takes one only
   argument (the class).
 * Fix GenericFieldSet.readMoreFields() result: don't count the number of
   added fields in a loop, use the number of fields before/after the operation
   using len()
 * GenericFieldSet.__iter__() supports iterable result for _fixFeedError() and
   _stopFeeding()
 * New seekable field set implementation in
   hachoir_core.field.new_seekable_field_set

hachoir-core 1.2.1 (2008-10)
============================

 * Create configuration option "unicode_stdout" which avoid replacing
   stdout and stderr by objects supporting unicode string
 * Create TimedeltaWin64 file type
 * Support WINDOWS-1252 and WINDOWS-1253 charsets for GenericString
 * guessBytesCharset() now supports ISO-8859-7 (greek)
 * durationWin64() is now deprecated, use TimedeltaWin64 instead

hachoir-core 1.2 (2008-09)
==========================

 * Create Field.getFieldType(): describe a field type and gives some useful
   informations (eg. the charset for a string)
 * Create TimestampUnix64
 * GenericString: only guess the charset once; if the charset attribute
   if not set, guess it when it's asked by the user.

hachoir-core 1.1 (2008-04-01)
=============================

Main change: string values are always encoded as Unicode. Details:

 * Create guessBytesCharset() and guessStreamCharset()
 * GenericString.createValue() is now always Unicode: if charset is not
   specified, try to guess it. Otherwise, use default charset (ISO-8859-1)
 * RawBits: add createRawDisplay() to avoid slow down on huge fields
 * Fix SeekableFieldSet.current_size (use offset and not current_max_size)
 * GenericString: fix UTF-16-LE string with missing nul byte
 * Add __nonzero__() method to GenericTimestamp
 * All stream errors now inherit from StreamError (instead of HachoirError),
   and create  and OutputStreamError
 * humanDatetime(): strip microseconds by default (add optional argument to
   keep them)

hachoir-core 1.0 (2007-07-10)
=============================

Version 1.0.1 changelog:
 * Rename parser.tags to parser.PARSER_TAGS to be compatible
   with future hachoir-parser 1.0

Visible changes:
 * New field type: TimestampUUID60
 * SeekableFieldSet: fix __getitem__() method and implement __iter__()
   and __len__() methods, so it can now be used in hachoir-wx
 * String value is always Unicode, even on conversion error: use
 * OutputStream: add readBytes() method
 * Create Language class using ISO-639-2
 * Add hachoir_core.profiler module to run a profiler on a function
 * Add hachoir_core.timeout module to call a function with a timeout

Minor changes:
 * Fix many spelling mistakes
 * Dict: use iteritems() instead of items() for faster operations on
   huge dictionaries


Hachoir Parser
^^^^^^^^^^^^^^

hachoir-parser 1.3.5
====================

 * torrent parser handles empty strings
 * fix issue #48: fix matroska parser, strip trailing null bytes

hachoir-parser 1.3.4 (2010-07-26)
=================================

 * update matroska parser to support WebM videos

hachoir-parser 1.3.3 (2010-04-15)
=================================

 * fix setup.py: don't use with statement to stay compatible with python 2.4

hachoir-parser 1.3.2 (2010-03-01)
=================================

 * Include the README file in the tarball
 * setup.py reads the README file instead of using README.py to break the
   build dependency on hachoir-core

hachoir-parser 1.3.1 (2010-01-28)
=================================

 * Create MANIFEST.in to include extra files: README.py, README.header,
   tests/run_testcase.py, etc.
 * Create an INSTALL file

hachoir-parser 1.3 (2010-01-20)
===============================

 * New parsers:

   - BLP: Blizzard Image
   - PRC: Palm resource

 * HachoirParserList() is no more a singleton:
   use HachoirParserList.getInstance() to get a singleton
 * Add tags optional argument to createParser(), it can be used for example to
   force a parser
 * Fix ParserList.print_(): first argument is now the title and not 'out'.
   If out is not specified, use sys.stdout.
 * MP3: support encapsulated objects (GEOB in ID3)
 * Create a dictionary: Windows codepage => charset name (CODEPAGE_CHARSET)
 * ASN.1: support boolean and enum types; fix bit string parser
 * MKV: use textHandler()
 * AVI: create index parser, use file size header to detect padding at the end
 * ISO9660: strip nul bytes in application name
 * JPEG: add ICC profile chunk name
 * PNG: fix transparency parser (tRNS)
 * BPLIST: support empty value for markers 4, 5 and 6
 * Microsoft Office summary: support more codepages (CP874, Windows 1250..1257)
 * tcpdump: support ICMPv6 and IPv6
 * Java: add bytecode parser, support JDK 1.6
 * Python: parse lnotab content, fill a string table for the references
 * MPEG Video: parse much more chunks
 * MOV: Parse file type header, create the right MIME type


hachoir-parser 1.2.1 (2008-10-16)
=================================

 * Improve OLE2 and MS Office parsers:
   - support small blocks
   - fix the charset of the summary properties
   - summary property integers are unsigned
   - use TimedeltaWin64 for the TotalEditingTime field
   - create minimum Word document parser
 * Python parser: support magic numbers of Python 3000
   with the keyword only arguments
 * Create Apple/NeXT Binary Property List (BPLIST) parser
 * MPEG audio: reject file with no valid frame nor ID3 header
 * Skip subfiles in JPEG files
 * Create Apple/NeXT Binary Property List (BPLIST) parser by Robert Xiao

hachoir-parser 1.2 (2008-09-03)
===============================

 * Create FLAC parser, written by Esteban Loiseau
 * Create Action Script parser used in Flash parser,
   written by Sebastien Ponce
 * Create Gnome Keyring parser: able to parse the stored passwords using
   Python Crypto if the main password is written in the code :-)
 * GIF: support text extension field; parse image content
   (LZW compressed data)
 * Fix charset of IPTC string (guess it, it's not always ISO-8859-1)
 * TIFF: Sebastien Ponce improved the parser: parse image data, add many
   tags, etc.
 * MS Office: guess the charset for summary strings since it could be
   ISO-8859-1 or UTF-8

hachoir-parser 1.1 (2008-04-01)
===============================

Main changes: add "EFI Platform Initialization Firmware
Volume" (PIFV) and "Microsoft Windows Help" (HLP) parsers. Details:

 * MPEG audio:

   - add createContentSize() to support hachoir-subfile
   - support file starting with ID3v1
   - if file doesn't contain any frame, use ID3v1 or ID3v2 to create the
     description

 * EXIF:

   - use "count" field value
   - create RationalInt32 and RationalUInt32
   - fix for empty value
   - add GPS tags

 * JPEG:

   - support Ducky (APP12) chunk
   - support Comment chunk
   - improve validate(): make sure that first 3 chunk types are known

 * RPM: use bzip2 or gzip handler to decompress content
 * S3M: fix some parser bugs
 * OLE2: reject negative block index (or special block index)
 * ip2name(): catch KeybordInterrupt and don't resolve next addresses
 * ELF: support big endian
 * PE: createContentSize() works on PE program, improve resource section
   detection
 * AMF: stop mixed array parser on empty key

hachoir-parser 1.0 (2007-07-11)
===============================

Changes:

 * OLE2: Support file bigger than 6 MB (support many DIFAT blocks)
 * OLE2: Add createContentSize() to guess content size
 * LNK: Improve parser (now able to parse the whole file)
 * EXE PE: Add more subsystem names
 * PYC: Support Python 2.5c2
 * Fix many spelling mistakes

Minor changes:

 * PYC: Fix long integer parser (negative number), add (disabled) code
   to disassemble bytecode, use self.code_info to avoid replacing self.info
 * OLE2: Add ".msi" file extension
 * OLE2: Fix to support documents generated on Mac
 * EXIF: set max IFD entry count to 1000 (instead of 200)
 * EXIF: don't limit BYTE/UNDEFINED IFD entry count
 * EXIF: add "User comment" tag
 * GIF: fix image and screen description
 * bzip2: catch decompressor error to be able to read trailing data
 * Fix file extensions of AIFF
 * Windows GUID use new TimestampUUID60 field type
 * RIFF: convert class constant names to upper case
 * Fix RIFF: don't replace self.info method
 * ISO9660: Write parser for terminator content


Hachoir Metadata
^^^^^^^^^^^^^^^^

hachoir-metadata 1.3.3 (2010-07-26)
===================================

 * Support WebM video (update Matroska extractor)
 * Matroska parser extracts audio bits per sample

hachoir-metadata 1.3.2 (2010-02-04)
===================================

 * Include hachoir_metadata/qt/dialog_ui.py in MANIFEST.in
 * setup.py ignores pyuic4 error if dialog_ui.py is present
 * setup.py installs hachoir_metadata.qt module

hachoir-metadata 1.3.1 (2010-01-28)
===================================

 * setup.py compiles dialog.ui to dialog_ui.py and install
   hachoir-metadata-qt. Create --disable-qt option to skip
   hachoir-metadata-qt installation.
 * Create a MANIFEST.in file to include extra files like ChangeLog, AUTHORS,
   gnome and kde subdirectories, test_doc.py, etc.

hachoir-metadata 1.3 (2010-01-20)
=================================

 * Create hachoir-metadata-qt: a graphical interface (Qt toolkit)
   to display files metadata
 * Create ISO9660 extractor
 * Hide Hachoir warnings by default (use --verbose to show them)
 * hachoir-metadata program: create --force-parser option to choose the parser

hachoir-metadata 1.2.1 (2008-10-16)
===================================

 * Using --raw, strings are not normalized (don't strip trailing space, new
   line, nul byte, etc.)
 * Extract much more informations from Microsoft Office documents (.doc, .xsl,
   .pps, etc.)
 * Improve OLE2 (Word) extractor
 * Fix ASF extractor for hachoir-parser 1.2.1

hachoir-metadata 1.2 (2008-09-03)
=================================

 * Create --maxlen option for hachoir-metadata program: --maxlen=0 disable
   the arbitrary string length limit
 * Create FLAC metadata extractor
 * Create hachoir_metadata.config, especially MAX_STR_LENGTH option
   (maximum string length)
 * GIF image may contains multiple comments

hachoir-metadata 1.1 (2008-04-01)
=================================

 * More extractors are more stable and fault tolerant
 * Create basic Gtk+ GUI: hachoir-metadata-gtk
 * Catch error on data conversion
 * Read width and height DPI for most image formats
 * JPEG (EXIF): read GPS informations
 * Each data item can has its own "setter"
 * Add more ID3 keys (TCOP, TDAT, TRDA, TORY, TIT1)
 * Create datetime filter supporting timezone
 * Add "meters", "pixels", "DPI" suffix for human display
 * Create SWF extractor
 * RIFF: read also informations from headers field, compute audio
   compression rate
 * MOV: read width and height
 * ASF: read album artist

hachoir-metadata 1.0.1 (???)
============================

 * Only use hachoir_core.profiler with --profiler command line option
   so 'profiler' Python module is now optional
 * Set shebang to "#!/usr/bin/python"

hachoir-metadata 1.0 (2007-07-11)
=================================

 * Real audio: read number of channel, bit rate, sample rate and
   compute compression rate
 * JPEG: Read user commment
 * Windows ANI: Read frame rate
 * Use Language from hachoir_core to store language from ID3 and MKV
 * OLE2 and FLV: Extractors are now fault tolerant

Hachoir Urwid
^^^^^^^^^^^^^

What's new in hachoir-urwid 1.1?
================================

 * Use the new getFieldType() method of hachoir-core 1.2 to display better
   informations about the field type, eg. shows the string charset

What's new in hachoir-urwid 1.0?
================================

Version 1.0.1
-------------

 * Only use hachoir_core.profiler with --profiler command line option
   so 'profiler' Python module is now optional
 * Set shebang to "#!/usr/bin/python"

Version 1.0
-----------

 * Compatible with hachoir-core 1.0 and hachoir-parser 1.0
 * Set default of preload to 15 (instead of 3)

What's new in hachoir-urwid 0.9.0?
==================================

Changes:

 * Fixes to support latest version of urwid
 * Updates to last version of hachoir-core and hachoir-parser (eg. use
   HachoirParserList class to display parser list)
 * Replace command line option --force-mime with --parser (value is now the
   parser identifier and not a MIME type)
 * Add command line options --hide-value and --hide-size

What's new in hachoir-urwid 0.8.0?
==================================

 * CTRL+E write field content to a file
 * CTRL+X create a stream from a field a write it into a file
 * Update to hachoir-core 0.8.0 (changes in input streams)
   and hachoir-parser 0.9.0 (way to choose the right parser)
 * Update to urwid 0.9.7.2 (use Unicode string)
 * Add option 'profile-display' to use Python profiler

What's new in hachoir-urwid 0.7.1?
==================================

 * setup.py doesn't depdend on hachoir-core, nor hachoir-parser, not urwid
 * setup.py uses distutils by default (and not setuptools)

What's new in hachoir-urwid 0.7?
================================

 * Support invalid unicode filename
 * Support decompression of a subfile
 * Better managment of "raw display"
 * Add command line option --parser-list

