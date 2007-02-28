#!/usr/bin/env python2.4
# -*- coding: utf-8 -*-
"""
Test hachoir-metadata using the testcase.
"""
DOWNLOAD_SCRIPT = "download_testcase.py"

# Configure Hachoir
from hachoir_core import config
config.use_i18n = False  # Don't use i18n
config.quiet = True      # Don't display warnings

from hachoir_core.i18n import getTerminalCharset
from hachoir_core.error import HachoirError
from hachoir_core.stream import InputStreamError
from hachoir_parser import createParser
from hachoir_core.compatibility import all
from hachoir_metadata import extractMetadata
import datetime
from locale import setlocale, LC_ALL
import os
import sys

def checkAttr(metadata, name, value):
    sys.stdout.write("  - Check metadata %s=%s: " % (name, repr(value)))

    if not isinstance(value, (list, tuple)):
        value = [value]

    # Has subgroup? (eg. "audio/sample_rate")
    if "/" in name:
        group, name = name.split("/", 1)
        if group not in metadata:
            sys.stdout.write("no group \"%s\"!\n" % group)
            return False
        metadata = metadata[group]

    # Has asked attribute?
    if not hasattr(metadata, name):
        sys.stdout.write("no attribute \"%s\"!\n" % name)
        return False

    # Read value
    read = getattr(metadata, name)

    # Check type
    if type(read) != type(value) \
    and (not isinstance(value, (int, long)) or not isinstance(value, (int, long))):
        sys.stdout.write("wrong type (%s instead of %s)!\n"
            % (type(read).__name__, type(value).__name__))
        return False

    # Check value
    if isinstance(read, (list, tuple)):
        if len(read) != len(value):
            sys.stdout.write("wrong len (%s instead of %s)!\n"
                % (len(read), len(value)))
            return False
        for index in xrange(len(value)):
            if value[index] != read[index]:
                sys.stdout.write("wrong value %s (%s instead of %s)!\n"
                    % (index, repr(read[index]), repr(value[index])))
                return False
    else:
        if value != read:
            sys.stdout.write("wrong value (%s)!\n" % repr(read))
            return False
    sys.stdout.write("ok\n")
    return True

def checkLogoUbuntuMeta(metadata): return (
    checkAttr(metadata, "bits_per_pixel", 8),
    checkAttr(metadata, "creation_date", "2006-05-26 09:41:46"),
    checkAttr(metadata, "mime_type", "image/png"))

def checkClickMeta(metadata): return (
    checkAttr(metadata, "producer", "Sound Forge 4.5"),
    checkAttr(metadata, "creation_date", "2001-02-21"),
    checkAttr(metadata, "duration", 19),
    checkAttr(metadata, "bit_rate", 705600),
    checkAttr(metadata, "sample_rate", 22050))

def checkGzipMeta(metadata): return (
    checkAttr(metadata, "file_size", 99),
    checkAttr(metadata, "compr_size", 90),
    checkAttr(metadata, "last_modification", u'2006-07-29 12:20:44'),
    checkAttr(metadata, "compression", "deflate"))

def checkSheepMeta(metadata): return (
    checkAttr(metadata, "format_version", "MPEG version 1 layer III"),
    checkAttr(metadata, "author", "Sheep On Drugs"),
    checkAttr(metadata, "comment", "Stainless Steel Provider is compilated to the car of Twinstar."))

def checkPng331_90_8Meta(metadata): return (
    checkAttr(metadata, "width", 331),
    checkAttr(metadata, "creation_date", u"2006-05-26 09:41:46"),
    checkAttr(metadata, "mime_type", "image/png"),
    checkAttr(metadata, "endian", u"Big endian"))

def checkFlashMobInfo(metadata): return (
    checkAttr(metadata, "copyright", u"© dadaprod, licence Creative Commons by-nc-sa 2.0 fr"),
    checkAttr(metadata, "video[1]/width", 384))

def checkCrossXCF(meta): return (
    checkAttr(meta, "comment", 'Created with The GIMP'),
    checkAttr(meta, "width", 61),
    checkAttr(meta, "height", 72),
    checkAttr(meta, "compression", "RLE"),
    checkAttr(meta, "mime_type", "image/x-xcf"))

def checkTARMeta(meta): return (
    checkAttr(meta, "file[0]/filename", "dummy.txt"),
    checkAttr(meta, "file[0]/file_size", 62),
    checkAttr(meta, "file[1]/file_attr", "-rwxr-xr-x (755)"),
    checkAttr(meta, "file[1]/last_modification", datetime.datetime(2006, 10, 1, 13, 9, 3)),
    checkAttr(meta, "file[2]/file_type", "Normal disk file"),
)

def checkCornerBMPMeta(meta): return (
    checkAttr(meta, "width", 189),
    checkAttr(meta, "nb_colors", 70),
    checkAttr(meta, "compression", "Uncompressed"),
    checkAttr(meta, "mime_type", "image/x-ms-bmp"),
)

def checkSmallville(metadata): return (
    checkAttr(metadata, "duration", 2641141),
    checkAttr(metadata, "producer", u"VirtualDubMod 1.5.10.1 (build 2366/release)"),
    checkAttr(metadata, "video/width", 640),
    checkAttr(metadata, "video/height", 352),
    checkAttr(metadata, "video/compression", u'XviD MPEG-4 (fourcc:"xvid")'),
    checkAttr(metadata, "video/frame_rate", 23.976),
    checkAttr(metadata, "audio[1]/nb_channel", 2),
    checkAttr(metadata, "audio[1]/sample_rate", 48000),
    checkAttr(metadata, "audio[1]/compression", u"MPEG Layer 3"))

def checkLechat(meta): return (
    checkAttr(meta, "album", [u"Arte Radio", u"Chat Broodthaers"]),
    checkAttr(meta, "url", "Liens direct ARTE Radio: www.arteradio.com/son.html?473"),
    checkAttr(meta, "creation_date", "2003"),
    checkAttr(meta, "producer", "www.arteradio.com"),
    checkAttr(meta, "sample_rate", 44100),
    checkAttr(meta, "bit_rate", 128000))

def checkJpegExifPSD(meta): return (
    checkAttr(meta, "producer", [u"Adobe Photoshop 7.0"]),
    checkAttr(meta, "width", 124),
    checkAttr(meta, "compression", "JPEG"),
    checkAttr(meta, "creation_date", "2006:06:28 14:51:09"))

def checkInterludeDavid(meta): return (
    checkAttr(meta, "title", u"interlude symbiosys1"),
    checkAttr(meta, "artist", u"david aubrun"),
    checkAttr(meta, "audio[1]/nb_channel", 2),
    checkAttr(meta, "audio[1]/format_version", "Vorbis version 0"),
    checkAttr(meta, "audio[1]/sample_rate", 44100),
)

def checkBreakdance(meta): return (
    checkAttr(meta, "duration", 46942.0),
    checkAttr(meta, "producer",
        [u"YouTube, Inc.", u"YouTube Metadata Injector."]),
)

def checkMatrixPingPong(meta): return (
    checkAttr(meta, "title", u"欽ちゃん＆香取慎吾の全日本仮装大賞"),
    checkAttr(meta, "duration", u'1 min 47 sec'),
    checkAttr(meta, "creation_date", u'2003-06-16 07:57:23.235000'),
    checkAttr(meta, "audio[1]/sample_rate", 8000),
    checkAttr(meta, "audio[1]/bits_per_sample", 16),
    checkAttr(meta, "audio[1]/compression", "Windows Media Audio V7 / V8 / V9"),
    checkAttr(meta, "video[1]/width", 200),
    checkAttr(meta, "video[1]/height", 150),
    checkAttr(meta, "video[1]/bits_per_pixel", 24),
)

def checkUSARailroad(meta): return (
    # Check IPTC parser
    checkAttr(meta, "author", u"Ian Britton"),
    checkAttr(meta, "copyright", u"FreeFoto.com"),
)

def checkHero(meta): return (
    checkAttr(meta, "width", 320),
    checkAttr(meta, "bits_per_pixel", 8),
    checkAttr(meta, "nb_colors", 256),
    checkAttr(meta, "compression", u"8-bit uncompressed"),
)

def checkFirstrun(meta): return (
    checkAttr(meta, "duration", 17066),
    checkAttr(meta, "creation_date", "6/14/2000 10:03:18"),
    checkAttr(meta, "copyright", u"©2000 RealNetworks"),
    checkAttr(meta, "producer", u"RealProducer Plus 6.1.0.153 Windows"),
    checkAttr(meta, "stream[1]/bit_rate", 32148),
    checkAttr(meta, "stream[1]/title", "Audio Stream"),
)

def check25min(meta): return (
    checkAttr(meta, "duration", 1533000),
    checkAttr(meta, "nb_channel", 2),
    checkAttr(meta, "sample_rate", 44100),
    checkAttr(meta, "bits_per_sample", 16),
    checkAttr(meta, "compression", u"Little-endian, no compression"),
)

def checkLadouce(meta): return (
    checkAttr(meta, "duration", 4592516),
    checkAttr(meta, "nb_channel", 6),
    checkAttr(meta, "sample_rate", 44100),
    checkAttr(meta, "bits_per_sample", 32),
    checkAttr(meta, "compression", "IEEE Float"),
    checkAttr(meta, "bit_rate", 8467200),
)

def checkLaraCroft(meta): return (
    checkAttr(meta, "width", 320),
    checkAttr(meta, "nb_colors", 256),
    checkAttr(meta, "compression", "Run-length encoding (RLE)"),
)

def checkHachoirOrgSXW(meta): return (
    checkAttr(meta, "mime_type", "application/vnd.sun.xml.writer"),
    checkAttr(meta, "file[0]/file_size", 30),
    checkAttr(meta, "file[1]/creation_date", u"2007-01-22 19:08:14"),
    checkAttr(meta, "file[2]/filename", u"Configurations2/accelerator/current.xml"),
    checkAttr(meta, "file[2]/compression", u"Deflate"),
)

def checkFirstRun(meta): return (
    checkAttr(meta, "mime_type", u"audio/x-pn-realaudio"),
    checkAttr(meta, "duration", 17066),
    checkAttr(meta, "creation_date", u"6/14/2000 10:03:18"),
    checkAttr(meta, "copyright", u"©2000 RealNetworks"),
    checkAttr(meta, "bit_rate", 32348),
    checkAttr(meta, "producer", u"RealProducer Plus 6.1.0.153 Windows"),
    checkAttr(meta, "stream[1]/title", u"Audio Stream"),
    checkAttr(meta, "stream[1]/mime_type", u"audio/x-pn-realaudio"),
    checkAttr(meta, "stream[2]/bit_rate", 200),
)

def checkDejaVu(meta): return (
    checkAttr(meta, "title", u"DejaVu Serif"),
    checkAttr(meta, "author", u"DejaVu fonts team"),
    checkAttr(meta, "version", u"Version 2.7"),
    checkAttr(meta, "creation_date", datetime.datetime(2006, 7, 6, 17, 29, 52)),
    checkAttr(meta, "last_modification", datetime.datetime(2006, 7, 6, 17, 29, 52)),
    checkAttr(meta, "copyright", [
        u"Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved.\nDejaVu changes are in public domain",
        u"http://dejavu.sourceforge.net/wiki/index.php/License"]),
    checkAttr(meta, "url", "http://dejavu.sourceforge.net"),
    checkAttr(meta, "comment", [
        u"Smallest readable size in pixels: 8 pixels",
        u"Font direction: Mixed directional"]),
)

def checkFile(filename, check_metadata):
    sys.stdout.write("  - Create parser: ")
    sys.stdout.flush()
    try:
        parser = createParser(filename)
    except InputStreamError, err:
        sys.stdout.write("stream error! %s\n" % unicode(err))
        sys.exit(1)
    if not parser:
        sys.stdout.write("unable to create parser\n")
        return False
    sys.stdout.write("ok\n")

    sys.stdout.write("  - Create metadata: ")
    sys.stdout.flush()
    try:
        metadata = extractMetadata(parser)
    except HachoirError, err:
        sys.stdout.write("stream error! %s\n" % unicode(err))
        sys.exit(1)
    if not metadata:
        sys.stdout.write("unable to create parser\n")
        return False
    sys.stdout.write("ok\n")

    if check_metadata is not True:
        return all(check_metadata(metadata))
    else:
        return True

def testFiles(directory):
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
        except OSError:
             print "Unable to create directory: %s" % directory
             return False

    for filename, check_metadata in testcase_files:
        fullname = os.path.join(directory, filename)
        try:
            os.stat(fullname)
        except OSError:
            print >>sys.stderr, \
                "[!] Error: file %s is missing, " \
                "use script %s to fix your testcase" \
                % (filename, DOWNLOAD_SCRIPT)
            return False
        print "[+] Test %s:" % filename
        if not checkFile(fullname, check_metadata):
            return False
    return True

def main():
    setlocale(LC_ALL, "C")
    if len(sys.argv) != 2:
        print >>sys.stderr, "usage: %s testcase_directory" % sys.argv[0]
        sys.exit(1)
    charset = getTerminalCharset()
    directory = unicode(sys.argv[1], charset)

    print "Test hachoir-metadata using testcase."
    print
    print "Testcase is in directory: %s" % directory
    ok = testFiles(directory)
    if ok:
        print
        print "Result: ok for the %s files" % len(testcase_files)
        sys.exit(0)
    else:
        print
        for index in xrange(3):
            print "!!! ERROR !!!"
        print
        sys.exit(1)

testcase_files = (
    (u"logo-kubuntu.png", checkLogoUbuntuMeta),
    (u"kde_click.wav", checkClickMeta),
    (u"test.txt.gz", checkGzipMeta),
    (u"flashmob.mkv", checkFlashMobInfo),
    (u"10min.mkv", True),
    (u"wormux_32x32_16c.ico", True),
    (u"audio_8khz_8bit_ulaw_4s39.au", True),
    (u"sheep_on_drugs.mp3", checkSheepMeta),
    (u"cross.xcf", checkCrossXCF),
    (u"small_text.tar", checkTARMeta),
    (u"kde_haypo_corner.bmp", checkCornerBMPMeta),
    (u"png_331x90x8_truncated.png", checkPng331_90_8Meta),
    (u"smallville.s03e02.avi", checkSmallville),
    (u"08lechat_hq_fr.mp3", checkLechat),
    (u"jpeg.exif.photoshop.jpg", checkJpegExifPSD),
    (u"interlude_david_aubrun.ogg", checkInterludeDavid),
    (u"breakdance.flv", checkBreakdance),
    (u"matrix_ping_pong.wmv", checkMatrixPingPong),
    (u"usa_railroad.jpg", checkUSARailroad),
    (u"hero.tga", checkHero),
    (u"firstrun.rm", checkFirstrun),
    (u"25min.aifc", check25min),
    (u"ladouce_1h15.wav", checkLadouce),
    (u"lara_croft.pcx", checkLaraCroft),
    (u"hachoir.org.sxw", checkHachoirOrgSXW),
    (u"firstrun.rm", checkFirstRun),
    (u"deja_vu_serif-2.7.ttf", checkDejaVu),
)

if __name__ == "__main__":
    main()

