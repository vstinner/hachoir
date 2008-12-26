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
from hachoir_core.language import Language
from hachoir_metadata import extractMetadata
from hachoir_metadata.timezone import createTimezone
from datetime import date, timedelta, datetime
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
    if not metadata.has(name):
        sys.stdout.write("no attribute \"%s\"!\n" % name)
        return False

    # Read value
    reads = metadata.getValues(name)

    # Check value
    if len(reads) != len(value):
        sys.stdout.write("wrong len (%s instead of %s)!\n"
            % (len(reads), len(value)))
        return False
    values = value
    for index, value in enumerate(values):
        read = reads[index]

        # Check type
        if type(read) != type(value) \
        and not(isinstance(value, (int, long)) and isinstance(value, (int, long))):
            sys.stdout.write("wrong type (%s instead of %s)!\n"
                % (type(read).__name__, type(value).__name__))
            return False

        # Check value
        if value != read:
            sys.stdout.write("wrong value %s (%r instead of %r)!\n"
                % (index, read, value))
            return False
    sys.stdout.write("ok\n")
    return True

def checkLogoUbuntuMeta(metadata): return (
    checkAttr(metadata, "bits_per_pixel", 32),
    checkAttr(metadata, "creation_date", datetime(2006, 5, 26, 9, 41, 46)),
    checkAttr(metadata, "mime_type", u"image/png"))

def checkClickMeta(metadata): return (
    checkAttr(metadata, "producer", u"Sound Forge 4.5"),
    checkAttr(metadata, "creation_date", date(2001, 2, 21)),
    checkAttr(metadata, "duration", timedelta(microseconds=19546)),
    checkAttr(metadata, "bit_rate", 705600),
    checkAttr(metadata, "sample_rate", 22050))

def checkGzipMeta(metadata): return (
    checkAttr(metadata, "file_size", 99),
    checkAttr(metadata, "compr_size", 90),
    checkAttr(metadata, "last_modification", datetime(2006, 7, 29, 12, 20, 44)),
    checkAttr(metadata, "os", u"Unix"),
    checkAttr(metadata, "compression", u"deflate"))

def checkSheepMeta(metadata): return (
    checkAttr(metadata, "format_version", u"MPEG version 1 layer III"),
    checkAttr(metadata, "author", u"Sheep On Drugs"),
    checkAttr(metadata, "comment", u"Stainless Steel Provider is compilated to the car of Twinstar."))

def checkPng331_90_8Meta(metadata): return (
    checkAttr(metadata, "width", 331),
    checkAttr(metadata, "creation_date", datetime(2006, 5, 26, 9, 41, 46)),
    checkAttr(metadata, "mime_type", u"image/png"),
    checkAttr(metadata, "endian", u"Big endian"))

def checkFlashMobInfo(metadata): return (
    checkAttr(metadata, "copyright", u"© dadaprod, licence Creative Commons by-nc-sa 2.0 fr"),
    checkAttr(metadata, "video[1]/width", 384),
    checkAttr(metadata, "video[1]/language", Language('fre')),
    checkAttr(metadata, "duration", timedelta(seconds=17, milliseconds=844)),
)

def check10min(meta): return (
    checkAttr(meta, "duration", timedelta(minutes=10)),
    checkAttr(meta, "producer", [u"x264", u"Haali Matroska Writer b0"]),
    checkAttr(meta, "video[1]/width", 384),
    checkAttr(meta, "video[1]/height", 288),
    checkAttr(meta, "video[1]/compression", u"V_MPEG4/ISO/AVC"),
)

def checkWormuxIco(meta): return (
    checkAttr(meta, "image[0]/width", 16),
    checkAttr(meta, "image[0]/height", 16),
    checkAttr(meta, "image[0]/bits_per_pixel", 32),
    checkAttr(meta, "image[0]/compression", u"Uncompressed (RGB)"),
)

def checkAudio8kHz(meta): return (
    checkAttr(meta, "mime_type", u"audio/basic"),
    checkAttr(meta, "nb_channel", 1),
    checkAttr(meta, "bits_per_sample", 8),
    checkAttr(meta, "bit_rate", 64096),
    checkAttr(meta, "sample_rate", 8012),
    checkAttr(meta, "compression", u"8-bit ISDN u-law"),
    checkAttr(meta, "comment", u"../tmp/temp.snd"),
    checkAttr(meta, "duration", timedelta(seconds=4, microseconds=391538)),
)

def checkCrossXCF(meta): return (
    checkAttr(meta, "comment", u"Created with The GIMP"),
    checkAttr(meta, "width", 61),
    checkAttr(meta, "height", 72),
    checkAttr(meta, "compression", u"RLE"),
    checkAttr(meta, "mime_type", u"image/x-xcf"))

def checkTARMeta(meta): return (
    checkAttr(meta, "file[0]/filename", u"dummy.txt"),
    checkAttr(meta, "file[0]/file_size", 62),
    checkAttr(meta, "file[1]/file_attr", u"-rwxr-xr-x (755)"),
    checkAttr(meta, "file[1]/last_modification", datetime(2006, 10, 1, 13, 9, 3)),
    checkAttr(meta, "file[2]/file_type", u"Normal disk file"),
)

def checkCornerBMPMeta(meta): return (
    checkAttr(meta, "width", 189),
    checkAttr(meta, "nb_colors", 70),
    checkAttr(meta, "compression", u"Uncompressed"),
    checkAttr(meta, "mime_type", u"image/x-ms-bmp"),
)

def checkSmallville(metadata): return (
    checkAttr(metadata, "duration", timedelta(minutes=44, seconds=1, microseconds=141141)),
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
    checkAttr(meta, "url", u"Liens direct ARTE Radio: www.arteradio.com/son.html?473"),
    checkAttr(meta, "creation_date", date(2003, 1, 1)),
    checkAttr(meta, "producer", u"www.arteradio.com"),
    checkAttr(meta, "sample_rate", 44100),
    checkAttr(meta, "bit_rate", 128000))

def checkJpegExifPSD(meta): return (
    checkAttr(meta, "producer", [u"Adobe Photoshop 7.0"]),
    checkAttr(meta, "width", 124),
    checkAttr(meta, "compression", u"JPEG (Progressive)"),
    checkAttr(meta, "creation_date", datetime(2006, 6, 28, 14, 51, 9)))

def checkInterludeDavid(meta): return (
    checkAttr(meta, "title", u"interlude symbiosys1"),
    checkAttr(meta, "artist", u"david aubrun"),
    checkAttr(meta, "duration", timedelta(minutes=1, seconds=12, microseconds=19592)),
    checkAttr(meta, "audio[1]/nb_channel", 2),
    checkAttr(meta, "audio[1]/format_version", u"Vorbis version 0"),
    checkAttr(meta, "audio[1]/sample_rate", 44100),
    checkAttr(meta, "mime_type", u"audio/vorbis"),
)

def checkBreakdance(meta): return (
    checkAttr(meta, "audio/sample_rate", 22050),
    checkAttr(meta, "duration", timedelta(seconds=46, milliseconds=942)),
    checkAttr(meta, "producer",
        [u"YouTube, Inc.", u"YouTube Metadata Injector."]),
)

def checkMatrixPingPong(meta): return (
    checkAttr(meta, "title", u"欽ちゃん＆香取慎吾の全日本仮装大賞"),
    checkAttr(meta, "duration", timedelta(minutes=1, seconds=47, milliseconds=258)),
    checkAttr(meta, "creation_date", datetime(2003, 6, 16, 7, 57, 23, 235000)),
    checkAttr(meta, "audio[1]/sample_rate", 8000),
    checkAttr(meta, "audio[1]/bits_per_sample", 16),
    checkAttr(meta, "audio[1]/compression", u"Windows Media Audio V7 / V8 / V9"),
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

def check25min(meta): return (
    checkAttr(meta, "duration", timedelta(minutes=25, seconds=33)),
    checkAttr(meta, "nb_channel", 2),
    checkAttr(meta, "sample_rate", 44100),
    checkAttr(meta, "bit_rate", 1411200),
    checkAttr(meta, "bits_per_sample", 16),
    checkAttr(meta, "compression", u"Little-endian, no compression"),
)

def checkLadouce(meta): return (
    checkAttr(meta, "duration", timedelta(hours=1, minutes=16, seconds=32, microseconds=516032)),
    checkAttr(meta, "nb_channel", 6),
    checkAttr(meta, "sample_rate", 44100),
    checkAttr(meta, "bits_per_sample", 32),
    checkAttr(meta, "compression", u"IEEE Float"),
    checkAttr(meta, "bit_rate", 8467200),
)

def checkLaraCroft(meta): return (
    checkAttr(meta, "width", 320),
    checkAttr(meta, "nb_colors", 256),
    checkAttr(meta, "compression", u"Run-length encoding (RLE)"),
)

def checkHachoirOrgSXW(meta): return (
    checkAttr(meta, "mime_type", u"application/vnd.sun.xml.writer"),
    checkAttr(meta, "file[0]/file_size", 30),
    checkAttr(meta, "file[1]/creation_date", datetime(2007, 1, 22, 19, 8, 14)),
    checkAttr(meta, "file[2]/filename", u"Configurations2/accelerator/current.xml"),
    checkAttr(meta, "file[2]/compression", u"Deflate"),
)

def checkFirstRun(meta): return (
    checkAttr(meta, "duration", timedelta(seconds=17, milliseconds=66)),
    checkAttr(meta, "creation_date", datetime(2000, 6, 14, 10, 3, 18)),
    checkAttr(meta, "copyright", u"©2000 RealNetworks"),
    checkAttr(meta, "producer", u"RealProducer Plus 6.1.0.153 Windows"),
    checkAttr(meta, "stream[0]/mime_type", u"audio/x-pn-realaudio"),
    checkAttr(meta, "stream[0]/bit_rate", 32148),
    checkAttr(meta, "stream[0]/title", u"Audio Stream"),
    checkAttr(meta, "mime_type", u"audio/x-pn-realaudio"),
    checkAttr(meta, "bit_rate", 32348),
    checkAttr(meta, "stream[1]/bit_rate", 200),
)

def checkDejaVu(meta): return (
    checkAttr(meta, "title", u"DejaVu Serif"),
    checkAttr(meta, "author", u"DejaVu fonts team"),
    checkAttr(meta, "version", u"2.7"),
    checkAttr(meta, "creation_date", datetime(2006, 7, 6, 17, 29, 52)),
    checkAttr(meta, "last_modification", datetime(2006, 7, 6, 17, 29, 52)),
    checkAttr(meta, "copyright", [
        u"Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved.\nDejaVu changes are in public domain",
        u"http://dejavu.sourceforge.net/wiki/index.php/License"]),
    checkAttr(meta, "url", u"http://dejavu.sourceforge.net"),
    checkAttr(meta, "comment", [
        u"Smallest readable size in pixels: 8 pixels",
        u"Font direction: Mixed directional"]),
)

def checkTwunk16(meta): return (
    checkAttr(meta, "title", [
        u"Twain_32.dll Client's 16-Bit Thunking Server",
        u"Twain Thunker"]),
    checkAttr(meta, "author", u"Twain Working Group"),
    checkAttr(meta, "version", u"1,7,0,0"),
    checkAttr(meta, "format_version", u"New-style executable: Dynamic-link library (DLL)"),
)

def checkDebianTorrent(meta): return (
    checkAttr(meta, "filename", u"debian-31r4-i386-binary-1.iso"),
    checkAttr(meta, "url", u"http://bttracker.acc.umu.se:6969/announce"),
    checkAttr(meta, "file_size", 669775872),
    checkAttr(meta, "creation_date", datetime(2006, 11, 16, 21, 44, 37)),
)

def checkGreenFire(meta): return (
    checkAttr(meta, 'height', 64),
    checkAttr(meta, 'bits_per_pixel', 32),
    checkAttr(meta, 'comment', (u"Intel(R) JPEG Library, version 1,5,4,36", u"JPEG quality: 80%")),
)

def checkMarcKravetz(meta): return (
    checkAttr(meta, 'creation_date', datetime(2007, 7, 19, 9, 3, 57, tzinfo=createTimezone(2))),
    checkAttr(meta, 'sample_rate', 48000),
    checkAttr(meta, 'compr_rate', 12.0),
    checkAttr(meta, 'album', u"France Culture - Le portrait du jour par Marc Kravetz"),
    checkAttr(meta, 'author', u"Marc Kravetz"),
    checkAttr(meta, 'duration', timedelta(0, 2, 400000)),
    checkAttr(meta, 'bit_rate', 128000),
    checkAttr(meta, 'track_number', 32),
    checkAttr(meta, 'bits_per_sample', 16),
    checkAttr(meta, 'copyright', u"Radio France"),
    checkAttr(meta, 'format_version', u"MPEG version 1 layer III"),
)

def checkPentax320(meta): return (
    checkAttr(meta, 'width', 320),
    checkAttr(meta, 'height', 240),
    checkAttr(meta, 'duration', timedelta(0, 4, 966667)),
    checkAttr(meta, 'creation_date', datetime(2005, 8, 11, 14, 3, 54)),
    checkAttr(meta, 'last_modification', datetime(2005, 8, 11, 14, 3, 54)),
)

def checkGPS(meta): return (
    checkAttr(meta, 'altitude', 78.0),
    checkAttr(meta, 'creation_date', datetime(2003, 5, 24, 22, 29, 14)),
    checkAttr(meta, 'latitude', 35.616019444444447),
    checkAttr(meta, 'longitude', 139.69731666666667),
    checkAttr(meta, 'camera_model', u'A5301T'),
    checkAttr(meta, 'camera_manufacturer', u'KDDI-TS'),
)

def checkAngelBear(meta): return (
    checkAttr(meta, 'title', u"Angel Bear"),
    checkAttr(meta, 'artist', u"Copyright ©Loraine Wauer-Ferus http://www.billybear4kids.com"),
    checkAttr(meta, 'frame_rate', 4.0),
)

def checkHotelCalifornia(meta): return (
    checkAttr(meta, 'title', u"Hotel California"),
    checkAttr(meta, 'artist', u"The Eagles"),
    checkAttr(meta, 'duration', timedelta(seconds=51, microseconds=512834)),
    checkAttr(meta, 'nb_channel', 2),
    checkAttr(meta, 'sample_rate', 44100),
    checkAttr(meta, 'bits_per_sample', 16),
    checkAttr(meta, 'producer', u'reference libFLAC 1.1.2 20050205'),
)

def checkRadpoor(meta): return (
    checkAttr(meta, 'title', u"\u062a\u0633\u062a"),
    checkAttr(meta, 'author', u'Soroosh Radpoor'),
    checkAttr(meta, 'creation_date', datetime(2008, 9, 2, 16, 8, 30)),
)

def checkQuicktime(meta): return (
    checkAttr(meta, 'width', 190),
    checkAttr(meta, 'height', 240),
    checkAttr(meta, 'creation_date', datetime(2005, 10, 28, 17, 46, 46)),
    checkAttr(meta, 'mime_type', u'video/mp4'),
)

def checkFile(filename, check_metadata, quality=1.0):
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
        metadata = extractMetadata(parser, quality)
    except HachoirError, err:
        sys.stdout.write("stream error! %s\n" % unicode(err))
        sys.exit(1)
    if not metadata:
        sys.stdout.write("unable to create parser\n")
        return False
    sys.stdout.write("ok\n")

    return all(check_metadata(metadata))

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
    (u"10min.mkv", check10min),
    (u"wormux_32x32_16c.ico", checkWormuxIco),
    (u"audio_8khz_8bit_ulaw_4s39.au", checkAudio8kHz),
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
    (u"25min.aifc", check25min),
    (u"ladouce_1h15.wav", checkLadouce),
    (u"lara_croft.pcx", checkLaraCroft),
    (u"hachoir.org.sxw", checkHachoirOrgSXW),
    (u"firstrun.rm", checkFirstRun),
    (u"deja_vu_serif-2.7.ttf", checkDejaVu),
    (u"twunk_16.exe", checkTwunk16),
    (u"debian-31r4-i386-binary-1.iso.torrent", checkDebianTorrent),
    (u"green_fire.jpg", checkGreenFire),
    (u"marc_kravetz.mp3", checkMarcKravetz),
    (u"pentax_320x240.mov", checkPentax320),
    (u"gps.jpg", checkGPS),
    (u"angle-bear-48x48.ani", checkAngelBear),
    (u"hotel_california.flac", checkHotelCalifornia),
    (u"radpoor.doc", checkRadpoor),
    (u"quicktime.mp4", checkQuicktime),
)

if __name__ == "__main__":
    main()

