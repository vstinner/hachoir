hachoir-metadata extracts metadata from multimedia files: music, picture,
video, but also archives. It supports most common file formats:

 * Archives: bzip2, gzip, zip, tar
 * Audio: MPEG audio ("MP3"), WAV, Sun/NeXT audio, Ogg/Vorbis (OGG), MIDI,
   AIFF, AIFC, Real audio (RA)
 * Image: BMP, CUR, EMF, ICO, GIF, JPEG, PCX, PNG, TGA, TIFF, WMF, XCF
 * Misc: Torrent
 * Program: EXE
 * Video: ASF format (WMV video), AVI, Matroska (MKV), Quicktime (MOV),
   Ogg/Theora, Real media (RM)

It tries to give as much information as possible. For some file formats,
it gives more information than libextractor for example, such as the RIFF
parser, which can extract creation date, software used to generate the file,
etc. But hachoir-metadata cannot guess informations. The most complex operation
is just to compute duration of a music using frame size and file size.

hachoir-metadata has three modes:

 * classic mode: extract metadata, you can use --level=LEVEL to limit quantity
   of information to display (and not to extract)
 * --type: show on one line the file format and most important informations
 * --mime: just display file MIME type

The command 'hachoir-metadata --mime' works like 'file --mime',
and 'hachoir-metadata --type' like 'file'. But today file command supports
more file formats then hachoir-metadata.

Website: http://bitbucket.org/haypo/hachoir/wiki/hachoir-metadata


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

Similar projects
================

 * Kaa - http://freevo.sourceforge.net/cgi-bin/freevo-2.0/Kaa (written in Python)
 * libextractor: http://gnunet.org/libextractor/ (written in C)

A *lot* of other libraries are written to read and/or write metadata in MP3
music and/or EXIF photo.

