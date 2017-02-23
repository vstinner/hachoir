.. _metadata:

++++++++++++++++++++++++
hachoir-metadata program
++++++++++++++++++++++++

The ``hachoir-metadata`` program is a tool to extract metadata from multimedia
files: videos, pictures, sounds, archives, etc. It supports most common file
formats:

* Archives: bzip2, gzip, zip, tar
* Audio: MPEG audio ("MP3"), WAV, Sun/NeXT audio, Ogg/Vorbis (OGG), MIDI,
  AIFF, AIFC, Real audio (RA)
* Image: BMP, CUR, EMF, ICO, GIF, JPEG, PCX, PNG, TGA, TIFF, WMF, XCF
* Misc: Torrent
* Program: EXE
* Video: ASF format (WMV video), AVI, Matroska (MKV), Quicktime (MOV),
  Ogg/Theora, Real media (RM)

Features:

* Gtk interface
* Plugins for Nautilus (Gnome) and Konqueror (KDE)
* Support invalid / truncated files
* Unicode compliant (charset ISO-8859-XX, UTF-8, UTF-16), convert string to
  your terminal charset
* Remove duplicate values and if a string is a substring of another, just keep
  the longest one
* Set priority to value, so it's possible to filter metadata (option --level)
* Only depends on [[hachoir-parser|hachoir-parser]] (and not on libmatroska,
  libmpeg2, libvorbis, etc.)

It tries to give as much information as possible. For some file formats,
it gives more information than libextractor for example, such as the RIFF
parser, which can extract creation date, software used to generate the file,
etc. But hachoir-metadata cannot guess informations. The most complex operation
is just to compute duration of a music using frame size and file size.

hachoir-metadata has three modes:

* classic mode: extract metadata, you can use --level=LEVEL to limit quantity
  of information to display (and not to extract)
* ``--type``: show on one line the file format and most important informations
* ``--mime``: just display file MIME type

The command ``hachoir-metadata --mime`` works like ``file --mime``, and
``hachoir-metadata --type`` like ``file``. But today file command supports more
file formats then hachoir-metadata.


Example
=======

Example on AVI video (RIFF file format)::

    $ hachoir-metadata pacte_des_gnous.avi
    Common:
    - Duration: 4 min 25 sec
    - Comment: Has audio/video index (248.9 KB)
    - MIME type: video/x-msvideo
    - Endian: Little endian
    Video stream:
    - Image width: 600
    - Image height: 480
    - Bits/pixel: 24
    - Compression: DivX v4 (fourcc:"divx")
    - Frame rate: 30.0
    Audio stream:
    - Channel: stereo
    - Sample rate: 22.1 KHz
    - Compression: MPEG Layer 3


Supported file formats
======================

Total: 33 file formats.

Archive
-------

* bzip2: bzip2 archive
* cab: Microsoft Cabinet archive
* gzip: gzip archive
* mar: Microsoft Archive
* tar: TAR archive
* zip: ZIP archive

Audio
-----

* aiff: Audio Interchange File Format (AIFF)
* mpeg_audio: MPEG audio version 1, 2, 2.5
* real_audio: Real audio (.ra)
* sun_next_snd: Sun/NeXT audio

Container
---------

* matroska: Matroska multimedia container
* ogg: Ogg multimedia container
* real_media: !RealMedia (rm) Container File
* riff: Microsoft RIFF container

Image
-----

* bmp: Microsoft bitmap (BMP) picture
* gif: GIF picture
* ico: Microsoft Windows icon or cursor
* jpeg: JPEG picture
* pcx: PC Paintbrush (PCX) picture
* png: Portable Network Graphics (PNG) picture
* psd: Photoshop (PSD) picture
* targa: Truevision Targa Graphic (TGA)
* tiff: TIFF picture
* wmf: Microsoft Windows Metafile (WMF)
* xcf: Gimp (XCF) picture

Misc
----

* ole2: Microsoft Office document
* pcf: X11 Portable Compiled Font (pcf)
* torrent: Torrent metainfo file
* ttf: !TrueType font

Program
-------

* exe: Microsoft Windows Portable Executable

Video
-----

* asf: Advanced Streaming Format (ASF), used for WMV (video) and WMA (audio)
* flv: Macromedia Flash video
* mov: Apple !QuickTime movie

Command line options
====================

Modes --mime and --type
=======================

Option --mime ask to just display file MIME type (works like UNIX
"file --mime" program)::

    $ hachoir-metadata --mime logo-Kubuntu.png sheep_on_drugs.mp3 wormux_32x32_16c.ico
    logo-Kubuntu.png: image/png
    sheep_on_drugs.mp3: audio/mpeg
    wormux_32x32_16c.ico: image/x-ico

Option --file display short description of file type (works like
UNIX "file" program)::

    $ hachoir-metadata --type logo-Kubuntu.png sheep_on_drugs.mp3 wormux_32x32_16c.ico
    logo-Kubuntu.png: PNG picture: 331x90x8 (alpha layer)
    sheep_on_drugs.mp3: MPEG v1 layer III, 128.0 Kbit/sec, 44.1 KHz, Joint stereo
    wormux_32x32_16c.ico: Microsoft Windows icon: 16x16x32

Modes --mime and --type
-----------------------

Option ``--mime`` ask to just display file MIME type::

    $ hachoir-metadata --mime logo-Kubuntu.png sheep_on_drugs.mp3 wormux_32x32_16c.ico
    logo-Kubuntu.png: image/png
    sheep_on_drugs.mp3: audio/mpeg
    wormux_32x32_16c.ico: image/x-ico

(it works like UNIX "file --mime" program)

Option ``--file`` display short description of file type::

    $ hachoir-metadata --type logo-Kubuntu.png sheep_on_drugs.mp3 wormux_32x32_16c.ico
    logo-Kubuntu.png: PNG picture: 331x90x8 (alpha layer)
    sheep_on_drugs.mp3: MPEG v1 layer III, 128.0 Kbit/sec, 44.1 KHz, Joint stereo
    wormux_32x32_16c.ico: Microsoft Windows icon: 16x16x32

(it works like UNIX "file" program)


Filter metadatas with --level
-----------------------------

hachoir-metadata is a too much verbose by default::

    $ hachoir-metadata logo-Kubuntu.png
    Image:
    - Image width: 331
    - Image height: 90
    - Bits/pixel: 8
    - Image format: Color index
    - Creation date: 2006-05-26 09:41:46
    - Compression: deflate
    - MIME type: image/png
    - Endian: Big endian

You can skip useless information (here, only until level 7)::

    $ hachoir-metadata --level=7 logo-Kubuntu.png
    Image:
    - Image width: 331
    - Image height: 90
    - Bits/pixel: 8
    - Image format: Color index
    - Creation date: 2006-05-26 09:41:46
    - Compression: deflate

Example to get most importation informations (level 3)::

    $ hachoir-metadata --level=3 logo-Kubuntu.png
    Image:
    - Image width: 331
    - Image height: 90
    - Bits/pixel: 8
    - Image format: Color index

Getting help: --help
--------------------

Use ``--help`` option to get full option list.


See also
========

Used by
-------

hachoir-metadata library is used by:

* `Plone4artist <http://plone.org/products/plone4artistsvideo/>`_
* `amplee <http://trac.defuze.org/wiki/amplee>`_ (implementation of the Atom Publishing Protocol, APP)
* `django-massmedia <https://github.com/callowayproject/django-massmedia>`_ (Calloway open source library)
* `pyrenamer <http://www.infinicode.org/code/pyrenamer/>`_

Informations
------------

* (fr) `DCMI Metadata Terms <http://dublincore.org/documents/dcmi-terms/>`_: Classification of meta-datas done by the //Dublin Core//
* (fr) `Dublin Core article on Openweb website <http://openweb.eu.org/articles/dublin_core/>`_
* (fr) `avi_ogminfo <http://www.xwing.info/index.php?p=avi_ogminfo>`_ : Informations about AVI and OGM files
* (en) `Xesam <http://wiki.freedesktop.org/wiki/XesamAbout>`_ (was Wasabi): common interface between programs extracting metadata

Libraries
---------

* (fr|en) `MediaInfo <http://mediainfo.sourceforge.net>`_ (GPL v2, C++)
* (en) `Mutagen <http://www.sacredchao.net/quodlibet/wiki/Development/Mutagen>`_: audio metadata tag reader and writer (Python)
* (en) `getid3 <http://getid3.sourceforge.net/>`_: Library written in PHP to extact meta-datas from several multimedia file formats (and not only MP3)
* (fr|en) `libextractor <http://gnunet.org/libextractor/>`_: Library dedicated to meta-data extraction. See also: (en) `Bader's Python binding <http://cheeseshop.python.org/pypi/Extractor>`_
* (en) `Kaa <http://freevo.sourceforge.net/cgi-bin/freevo-2.0/Kaa>`_ (part of Freevo), it replaces `mmpython (Media Metadata for Python) <http://sourceforge.net/projects/mmpython/>`_ (dead project)
* (en) `ExifTool <http://search.cpan.org/~exiftool/Image-ExifTool-6.29/exiftool>`_: Perl library to read and write metadata

Programs
--------

* jpeginfo
* ogginfo
* mkvinfo
* mp3info

Programs using metadata
-----------------------

* Programs using metadata:

  - `GLScube <http://www.glscube.org/>`_
  - `Beagle <http://beagle-project.org/>`_ (`Kerry <http://kde-apps.org/content/show.php?content=36832>`_)
  - `Beagle++ <http://beagle.kbs.uni-hannover.de/>`_
  - `Nepomuk <http://nepomuk-kde.semanticdesktop.org/xwiki/bin/view/Main/KMetaData>`_

* Extractors:

  - `Tracker <http://www.tracker-project.org/>`_
  - `Strigi <http://www.vandenoever.info/software/strigi/>`_

* Other: `Lucene <http://lucene.apache.org/>`_ (full text search)


Metadata examples
=================

:ref:`hachoir-metadata <metadata>` (version 0.10) output examples.

Video
-----

AVI
^^^

Common:
 * Duration: 1 hour 38 min 4 sec
 * Image width: 576
 * Image height: 240
 * Frame rate: 25.0 fps
 * Bit rate: 989.9 Kbit/sec
 * Producer: Nandub v1.0rc2
 * Comment: Has audio/video index (5.7 MB)
 * MIME type: video/x-msvideo
 * Endian: Little endian
Video stream:
 * Duration: 1 hour 38 min 4 sec
 * Image width: 576
 * Image height: 240
 * Bits/pixel: 24
 * Compression: XviD MPEG-4 (fourcc:"xvid")
 * Frame rate: 25.0 fps
Audio stream:
 * Duration: 1 hour 38 min 4 sec
 * Channel: stereo
 * Sample rate: 44.1 kHz
 * Compression: MPEG Layer 3
 * Bit rate: 128.0 Kbit/sec

WMV
^^^

Common:
 * Title: 欽ちゃん＆香取慎吾の全日本仮装大賞
 * Author: Nippon Television Network Corporation[[NTV]
 * Duration: 1 min 47 sec 258 ms
 * Creation date: 2003-06-16 07:57:23.235000
 * Copyright: [C]]Nippon Television Network Corporation[NTV] 2003
 * Bit rate: 276.9 Kbit/sec (max)
 * Comment: Is seekable
 * MIME type: video/x-ms-wmv
 * Endian: Little endian
Audio stream !#1:
 * Channel: stereo
 * Sample rate: 8.0 kHz
 * Bits/sample: 16 bits
 * Compression: Windows Media Audio V7 / V8 / V9
 * Bit rate: 13.0 Kbit/sec
Video stream !#1:
 * Image width: 200
 * Image height: 150
 * Bits/pixel: 24
 * Compression: Windows Media Video V7
 * Bit rate: 16.3 Kbit/sec
Video stream !#2:
 * Image width: 200
 * Image height: 150
 * Bits/pixel: 24
 * Compression: Windows Media Video V7
 * Bit rate: 36.3 Kbit/sec
Video stream !#3:
 * Image width: 200
 * Image height: 150
 * Bits/pixel: 24
 * Compression: Windows Media Video V7
 * Bit rate: 211.3 Kbit/sec

MKV
^^^

Common:
 * Duration: 17 sec 844 ms
 * Creation date: 2006-08-16 11:04:36
 * Producer: mkvmerge v1.7.0 ('What Do You Take Me For') built on Jun  7 2006 08:33:28
 * Producer: libebml v0.7.7 + libmatroska v0.8.0
 * MIME type: video/x-matroska
 * Endian: Big endian
Video stream:
 * Language: French
 * Image width: 384
 * Image height: 288
 * Compression: V_MPEG4/ISO/AVC
Audio stream:
 * Title: travail = aliénation (extrait)
 * Language: French
 * Channel: mono
 * Sample rate: 44.1 kHz
 * Compression: A_VORBIS

FLV
^^^

Common:
 * Duration: 46 sec 942 ms
 * Bit rate: 287.4 Kbit/sec
 * Producer: !YouTube, Inc.
 * Producer: !YouTube Metadata Injector.
 * Format version: Macromedia Flash video version 1
 * MIME type: video/x-flv
 * Endian: Big endian
Metadata:
 * Channel: mono
 * Sample rate: 22.1 kHz
 * Bits/sample: 16 bits
 * Compression: MPEG-2 layer III, 64.0 Kbit/sec, 22.1 kHz
Metadata:
 * Compression: Sorensen H.263

Audio
-----

MP3
^^^

Metadata:
 * Title: 07. motorbike
 * Author: Sheep On Drugs
 * Album: Bilmusik vol 1. Stainless Steel Providers
 * Duration: 1 sec 301 ms
 * Music genre: Car music
 * Track number: 7
 * Track total: 13
 * Channel: Joint stereo
 * Sample rate: 44.1 kHz
 * Bits/sample: 16 bits
 * Compression rate: 11.0x
 * Creation date: 2003
 * Bit rate: 128.0 Kbit/sec (constant)
 * Comment: Stainless Steel Provider is compilated to the car of Twinstar.
 * Format version: MPEG version 1 layer III
 * MIME type: audio/mpeg
 * Endian: Big endian

Ogg Vorbis
^^^^^^^^^^

Common:
 * Title: La mouche
 * Album: Dans le caillou
 * Duration: 2 min 59 sec 893 ms
 * Music genre: Chanson
 * Track number: 6
 * Artist: Karpatt
 * Creation date: 2004
 * Producer: Xiph.Org libVorbis I 20050304
 * MIME type: audio/vorbis
 * Endian: Little endian
Audio:
 * Channel: stereo
 * Sample rate: 44.1 kHz
 * Compression: Vorbis
 * Bit rate: 128.0 Kbit/sec
 * Format version: Vorbis version 0

Picture
-------

JPEG
^^^^

Common:
 * Image width: 2048
 * Image height: 1536
 * Image orientation: Horizontal (normal)
 * Bits/pixel: 24
 * Pixel format: YCbCr
 * Compression rate: 15.5x
 * Camera aperture: 3
 * Camera focal: 2.8
 * Camera exposure: 1/60.1
 * Camera model: E3100
 * Camera manufacturer: NIKON
 * Compression: JPEG (Baseline)
 * Producer: E3100v1.2
 * Comment: JPEG quality: 85%
 * Format version: JFIF 1.01
 * MIME type: image/jpeg
 * Endian: Big endian

PNG
^^^

Metadata:
 * Image width: 331
 * Image height: 90
 * Bits/pixel: 32
 * Pixel format: RGBA
 * Compression rate: 12.0x
 * Creation date: 2006-05-26 09:41:46
 * Compression: deflate
 * MIME type: image/png
 * Endian: Big endian

ICO
^^^

Common:
 * MIME type: image/x-ico
 * Endian: Little endian
Icon !#1 (16x16):
 * Image width: 16
 * Image height: 16
 * Bits/pixel: 32
 * Compression rate: 0.9x
 * Compression: Uncompressed (RGB)

Archive
-------

CAB
^^^

Common:
 * Compression: LZX (level 16)
 * Comment: 1 folders, 6 files
 * Format version: Microsoft Cabinet version 0x0103
 * MIME type: application/vnd.ms-cab-compressed
 * Endian: Little endian
File "fontinst.inf":
 * File name: fontinst.inf
 * File size: 64 bytes
 * Creation date: 1998-11-10 16:09:52
File "Georgiaz.TTF":
 * File name: Georgiaz.TTF
 * File size: 155.1 KB
 * File attributes: archive
 * Creation date: 1998-11-10 14:00:02
File "Georgiab.TTF":
 * File name: Georgiab.TTF
 * File size: 136.3 KB
 * File attributes: archive
 * Creation date: 1998-11-10 14:00:02

Misc
----

TTF
^^^

Metadata:
 * Title: !DejaVu Serif
 * Author: !DejaVu fonts team
 * Version: 2.7
 * Creation date: 2006-07-06 17:29:52
 * Last modification: 2006-07-06 17:29:52
 * Copyright: Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved.\nDejaVu changes are in public domain
 * Copyright: !http://dejavu.sourceforge.net/wiki/index.php/License
 * URL: !http://dejavu.sourceforge.net
 * Comment: Smallest readable size in pixels: 8 pixels
 * Comment: Font direction: Mixed directional
 * MIME type: application/octet-stream
 * Endian: Big endian

EXE (PE)
^^^^^^^^

Metadata:
 * Title: EULA
 * Author: Dell Inc
 * Version: 1.00
 * Creation date: 2006-08-09 03:23:10
 * Comment: CPU: Intel 80386
 * Comment: Subsystem: Windows/GUI
 * Format version: Portable Executable: Windows application
 * MIME type: application/x-dosexec
 * Endian: Little endian

Torrent
^^^^^^^

Metadata:
 * File name: debian-31r4-i386-binary-1.iso
 * File size: 638.7 MB
 * Creation date: 2006-11-16 21:44:37
 * URL: !http://bttracker.acc.umu.se:6969/announce
 * Comment: "Debian CD from cdimage.debian.org"
 * Comment: Piece length: 512.0 KB
 * MIME type: application/x-bittorrent
 * Endian: Little endian
