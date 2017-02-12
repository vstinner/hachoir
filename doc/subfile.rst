+++++++++++++++++++++++
hachoir-subfile program
+++++++++++++++++++++++

hachoir-subfile is a tool based on hachoir-parser to find subfiles in any binary stream.

Changelog
=========

Version 0.5.3 (2008-04-01):

 * Catch StreamError on file copy
 * Use "#!/usr/bin/env python" as shebang for FreeBSD

Version 0.5.2 (2007-07-13):

 * Fix shebang: use "#!/usr/bin/python"
 * Only import hachoir_core.profiler with --profiler command line
   option is used, so hachoir-subfile do not depends on 'profiler'
   Python module

Version 0.5.1 (2007-07-12):

 * Fix setup.py: also install script 'hachoir-subfile'

Version 0.5 (2007-07-11):

 * Publication of the first public version

Usage
=====

Search JPEG images::

    hachoir-subfile input --parser=jpeg

Search images::

    hachoir-subfile input --category=image

Search images, videos and SWF files::

    hachoir-subfile input --category=image,video --parser=swf

Search all subfiles and store them in ``/tmp/subfiles/``::

    hachoir-subfile input /tmp/subfiles/

Other options:

* --offset: start search at specified offset in bytes
* --size: limit search to specified size in bytes

Search speed is proportional to the number of used parsers.


How does it work?
=================

Find file start
---------------

To find file start, hachoir-subfile use "magic number": short string (2 to 16
bytes) typical to a file format. Examples:

 * "MZ" for MS-Dos (and Windows) executable
 * "\xFF\xD8\xFF" for JPEG
 * "FAT16   " for FAT16 file system

When a magic number is found, a parser of hachoir parser is opened. The
validate() method is used to make sure that the file is in the right file
format. Some values of the header are tested:

 * TAR archive: check magic number, check first file entry (user/group
   identifier, file size)
 * SWF animation: check magic number, check version, check rectangle padding
   value
 * etc.

Find file length
----------------

To find (guess) file length, each parser requires a method called
"createContentSize()". Examples:

 * RIFF container: read "/filesize" field value
 * JPEG picture: search "\xFF\xD9" (End of image chunk) string
 * etc.


Examples
========

Find files in a hard drive::

    $ hachoir-subfile /dev/sda --size=34200100 --quiet
    [+] Start search (32.6 MB)

    [+] Found file at 0: MS-DOS hard drive with Master Boot Record (MBR)
    [+] Found file at 32256: FAT16 filesystem
    [+] Found file at 346112 size=308280 (301.1 KB): Microsoft Bitmap version 3
    [+] Found file at 32157696: MS-DOS executable
    [+] Found file at 32483328: MS-DOS executable
    [+] Found file at 32800768: MS-DOS executable
    [+] Found file at 32851968: MS-DOS executable
    [+] Found file at 32872448: MS-DOS executable
    [+] Found file at 33058816: MS-DOS executable
    [+] Found file at 33112064: MS-DOS executable
    [+] Found file at 33142784: MS-DOS executable
    [+] Found file at 33949936: Microsoft Windows Portable Executable: Intel 80386 or greater

    [+] Search done -- offset=34200100 (32.6 MB)
    Total time: 20.08 sec -- 1.6 MB/sec


PowerPoint document::

    $ hachoir-subfile chiens.PPS
    [+] Start search (828.5 KB)

    [+] Found file at 0: Microsoft Office document
    [+] Found file at 537 size=28449 (27.8 KB): JPEG picture: 433x300 pixels
    [+] Found file at 29011 size=34761 (33.9 KB): JPEG picture: 433x300 pixels
    [+] Found file at 63797 size=40326 (39.4 KB): JPEG picture: 433x300 pixels
    [+] Found file at 104148 size=30641 (29.9 KB): JPEG picture: 433x300 pixels
    [+] Found file at 134814 size=22782 (22.2 KB): JPEG picture: 384x325 pixels
    [+] Found file at 157621 size=24744 (24.2 KB): JPEG picture: 443x313 pixels
    [+] Found file at 182390 size=27241 (26.6 KB): JPEG picture: 443x290 pixels
    [+] Found file at 209656 size=27407 (26.8 KB): JPEG picture: 443x336 pixels
    [+] Found file at 237088 size=30088 (29.4 KB): JPEG picture: 388x336 pixels
    [+] Found file at 267201 size=30239 (29.5 KB): JPEG picture: 366x336 pixels
    [+] Found file at 297465 size=81634 (79.7 KB): JPEG picture: 630x472 pixels
    [+] Found file at 379124 size=36142 (35.3 KB): JPEG picture: 599x432 pixels
    [+] Found file at 415291 size=28801 (28.1 KB): JPEG picture: 443x303 pixels
    [+] Found file at 444117 size=28283 (27.6 KB): JPEG picture: 433x300 pixels
    [+] Found file at 472425 size=95913 (93.7 KB): PNG picture: 433x431x8
    [+] Found file at 568363 size=219252 (214.1 KB): PNG picture: 532x390x8
    [+] Found file at 811308 size=20644 (20.2 KB): Microsoft Windows Metafile (WMF) picture

    [+] Search done -- offset=848384 (828.5 KB)
    Total time: 1.30 sec -- 635.1 KB/sec


Filter
======

It's possible to filter files using your own function. Example to skip images
smaller than 256x256::

    from hachoir_metadata import extractMetadata
    import sys

    def metadataFilter(parser):
        try:
            metadata = extractMetadata(parser)
        except HachoirError, err:
            metadata = None

        if metadata:
            if hasattr(metadata, "width") and metadata.width[0]] < 256:
                print("Skip picture with width < 256 pixels", file=sys.stderr)
                return False
            if hasattr(metadata, "height") and metadata.height[[0]|< 256:
                print("Skip picture with height < 256 pixels", file=sys.stderr)
                return False
        return True

    subfile = HachoirSubfile(...)
    subfile.filter = metadataFilter
