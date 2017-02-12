+++++++++++++++++++++
hachoir.parser module
+++++++++++++++++++++

``hachoir.parser`` is a package of most common file format parsers written for
Hachoir framework. Not all parsers are complete, some are very good and other
are poor: only parser first level of the tree for example.

A perfect parser have no "raw" field: with a perfect parser you are able to
know *each* bit meaning. Some good (but not perfect ;-)) parsers:

* Matroska video
* Microsoft RIFF (AVI video, WAV audio, CDA file)
* PNG picture
* TAR and ZIP archive

Parser list
===========

Archive
-------

* 7zip: Compressed archive in 7z format
* ace: ACE archive
* bom_store: Apple bill-of-materials file
* bzip2: bzip2 archive
* cab: Microsoft Cabinet archive
* gzip: gzip archive
* mar: Microsoft Archive
* mozilla_ar: Mozilla Archive
* prs_pak: Parallel Realities Starfighter .pak archive
* rar: Roshal archive (RAR)
* rpm: RPM package
* tar: TAR archive
* unix_archive: Unix archive
* zip: ZIP archive
* zlib: ZLIB Data

Audio
-----

* aiff: Audio Interchange File Format (AIFF)
* fasttracker2: FastTracker2 module
* flac: FLAC audio
* itunesdb: iPod iTunesDB file
* midi: MIDI audio
* mod: Uncompressed amiga module
* mpeg_audio: MPEG audio version 1, 2, 2.5
* ptm: PolyTracker module (v1.17)
* real_audio: Real audio (.ra)
* s3m: ScreamTracker3 module
* sun_next_snd: Sun/NeXT audio

Container
---------

* asn1: Abstract Syntax Notation One (ASN.1)
* matroska: Matroska multimedia container
* ogg: Ogg multimedia container
* ogg_stream: Ogg logical stream
* real_media: RealMedia (rm) Container File
* riff: Microsoft RIFF container
* swf: Macromedia Flash data

File System
-----------

* ext2: EXT2/EXT3 file system
* fat12: FAT12 filesystem
* fat16: FAT16 filesystem
* fat32: FAT32 filesystem
* iso9660: ISO 9660 file system
* linux_swap: Linux swap file
* msdos_harddrive: MS-DOS hard drive with Master Boot Record (MBR)
* ntfs: NTFS file system
* reiserfs: ReiserFS file system

Game
----

* blp1: Blizzard Image Format, version 1
* blp2: Blizzard Image Format, version 2
* lucasarts_font: LucasArts Font
* spiderman_video: The Amazing Spider-Man vs. The Kingpin (Sega CD) FMV video
* zsnes: ZSNES Save State File (only version 143)

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

* 3do: renderdroid 3d model.
* 3ds: 3D Studio Max model
* bplist: Apple/NeXT Binary Property List
* chm: Microsoft's HTML Help (.chm)
* dsstore: Mac OS X DS_Store
* gnomekeyring: Gnome keyring
* hlp: Microsoft Windows Help (HLP)
* lnk: Windows Shortcut (.lnk)
* mapsforge_map: Mapsforge map file
* mstask: .job 'at' file parser from ms windows
* ole2: Microsoft Office document
* pcf: X11 Portable Compiled Font (pcf)
* pdf: Portable Document Format (PDF) document
* tcpdump: Tcpdump file (network)
* torrent: Torrent metainfo file
* ttf: TrueType font

Program
-------

* elf: ELF Unix/BSD program/library
* exe: Microsoft Windows Portable Executable
* java_class: Compiled Java class
* java_serialized: Serialized Java object
* macho: Mach-O program/library
* macho_fat: Mach-O fat program/library
* nds_file: Nintendo DS game file
* pifv: EFI Platform Initialization Firmware Volume
* prc: Palm Resource File
* python: Compiled Python script (.pyc/.pyo files)

Video
-----

* asf: Advanced Streaming Format (ASF), used for WMV (video) and WMA (audio)
* flv: Macromedia Flash video
* mov: Apple QuickTime movie
* mpeg_ts: MPEG-2 Transport Stream
* mpeg_video: MPEG video, version 1 or 2

Total: 91 parsers
