#!/usr/bin/env python3
"""
Test hachoir-metadata using the testcase.
"""

from hachoir.parser import createParser
from hachoir.core.language import Language
from hachoir.metadata import extractMetadata
from hachoir.metadata.timezone import createTimezone
from hachoir.test import setup_tests
from datetime import date, timedelta, datetime
import os
import subprocess
import sys
import unittest

DATADIR = os.path.join(os.path.dirname(__file__), 'files')
PROGRAM = os.path.join(os.path.dirname(__file__), "..", "hachoir-metadata")


class TestMetadata(unittest.TestCase):
    verbose = False

    def extract(self, filename):
        if self.verbose:
            print("[+] Test %s:" % filename)
            sys.stdout.write("  - Create parser: ")
            sys.stdout.flush()

        fullname = os.path.join(DATADIR, filename)
        parser = createParser(fullname)
        if not parser:
            self.fail("unable to create parser\n")

        with parser:
            if self.verbose:
                sys.stdout.write("ok\n")
                sys.stdout.write("  - Create metadata: ")
                sys.stdout.flush()

            metadata = extractMetadata(parser, 1.0)
            if not metadata:
                self.fail("unable to create parser\n")

        if self.verbose:
            sys.stdout.write("ok\n")
        return metadata

    def test_dict_output(self):
        required_meta = {'Common': {'duration': '0:00:17.844000',
                                    'creation_date': '2006-08-16 11:04:36',
                                    'producer': 'libebml v0.7.7 + libmatroska v0.8.0',
                                    'mime_type': 'video/x-matroska',
                                    'endian': 'Big endian'
                                    },
                         'video[1]': {'language': 'French',
                                      'width': '384',
                                      'height': '288',
                                      'compression': 'V_MPEG4/ISO/AVC'
                                      },
                         'audio[1]': {'title': 'travail = aliénation (extrait)',
                                      'language': 'French',
                                      'nb_channel': '1',
                                      'sample_rate': '44100.0',
                                      'compression': 'A_VORBIS'
                                      }
                         }
        with createParser(os.path.join(DATADIR, "flashmob.mkv")) as parser:
            extractor = extractMetadata(parser)
        meta = extractor.exportDictionary(human=False)

        self.assertEqual(required_meta, meta)

    def test_plaintext_output(self):
        expected_plaintext = [['Video stream:',
                               '- Language: French',
                               '- Image width: 384 pixels',
                               '- Image height: 288 pixels',
                               '- Compression: V_MPEG4/ISO/AVC'],
                              ['Audio stream:',
                               '- Title: travail = aliénation (extrait)',
                               '- Language: French',
                               '- Channel: mono',
                               '- Sample rate: 44.1 kHz',
                               '- Compression: A_VORBIS']]
        with createParser(os.path.join(DATADIR, "flashmob.mkv")) as parser:
            extractor = extractMetadata(parser)
        groups = [g.exportPlaintext() for g in extractor.iterGroups()]
        self.assertEqual(groups, expected_plaintext)

    def check_attr(self, metadata, name, value):
        if self.verbose:
            sys.stdout.write("  - Check metadata %s=%s: " %
                             (name, repr(value)))

        if not isinstance(value, (list, tuple)):
            value = [value]

        # Has subgroup? (eg. "audio/sample_rate")
        if "/" in name:
            group, name = name.split("/", 1)
            if group not in metadata:
                if self.verbose:
                    sys.stdout.write("no group \"%s\"!\n" % group)
                return False
            metadata = metadata[group]

        # Has asked attribute?
        if not metadata.has(name):
            if self.verbose:
                sys.stdout.write("no attribute \"%s\"!\n" % name)
            return False

        # Read value
        reads = metadata.getValues(name)

        # Check value
        if len(reads) != len(value):
            if self.verbose:
                sys.stdout.write("wrong len (%s instead of %s)!\n"
                                 % (len(reads), len(value)))
            return False
        values = value
        for index, value in enumerate(values):
            read = reads[index]

            # Check type
            if type(read) != type(value) \
                    and not(isinstance(value, int) and isinstance(value, int)):
                if self.verbose:
                    sys.stdout.write("wrong type (%s instead of %s)!\n"
                                     % (type(read).__name__, type(value).__name__))
                return False

            # Check value
            if value != read:
                if self.verbose:
                    sys.stdout.write("wrong value %s (%r instead of %r)!\n"
                                     % (index, read, value))
                return False
        if self.verbose:
            sys.stdout.write("ok\n")
        return True

    def test_png(self):
        metadata = self.extract("logo-kubuntu.png")
        self.check_attr(metadata, "bits_per_pixel", 32)
        self.check_attr(metadata, "creation_date",
                        datetime(2006, 5, 26, 9, 41, 46))
        self.check_attr(metadata, "mime_type", "image/png")

    def test_wav(self):
        metadata = self.extract("kde_click.wav")
        self.check_attr(metadata, "producer", "Sound Forge 4.5")
        self.check_attr(metadata, "creation_date", date(2001, 2, 21))
        self.check_attr(metadata, "duration", timedelta(microseconds=19546))
        self.check_attr(metadata, "bit_rate", 705600)
        self.check_attr(metadata, "sample_rate", 22050)

    def test_gzip(self):
        metadata = self.extract("test.txt.gz")
        self.check_attr(metadata, "file_size", 99)
        self.check_attr(metadata, "compr_size", 90)
        self.check_attr(metadata, "last_modification",
                        datetime(2006, 7, 29, 12, 20, 44))
        self.check_attr(metadata, "os", "Unix")
        self.check_attr(metadata, "compression", "deflate")

    def test_mp3(self):
        metadata = self.extract("sheep_on_drugs.mp3")
        self.check_attr(metadata, "format_version", "MPEG version 1 layer III")
        self.check_attr(metadata, "author", "Sheep On Drugs")
        self.check_attr(
            metadata, "comment", "Stainless Steel Provider is compilated to the car of Twinstar.")

    def test_png2(self):
        metadata = self.extract("png_331x90x8_truncated.png")
        self.check_attr(metadata, "width", 331)
        self.check_attr(metadata, "creation_date",
                        datetime(2006, 5, 26, 9, 41, 46))
        self.check_attr(metadata, "mime_type", "image/png")
        self.check_attr(metadata, "endian", "Big endian")

    def test_mkv(self):
        metadata = self.extract("flashmob.mkv")
        self.check_attr(metadata, "copyright",
                        "© dadaprod, licence Creative Commons by-nc-sa 2.0 fr")
        self.check_attr(metadata, "video[1]/width", 384)
        self.check_attr(metadata, "video[1]/language", Language('fre'))
        self.check_attr(metadata, "duration", timedelta(
            seconds=17, milliseconds=844))

    def test_mkv2(self):
        meta = self.extract("10min.mkv")
        self.check_attr(meta, "duration", timedelta(minutes=10))
        self.check_attr(meta, "producer", ["x264", "Haali Matroska Writer b0"])
        self.check_attr(meta, "video[1]/width", 384)
        self.check_attr(meta, "video[1]/height", 288)
        self.check_attr(meta, "video[1]/compression", "V_MPEG4/ISO/AVC")

    def test_ico(self):
        meta = self.extract("wormux_32x32_16c.ico")
        self.check_attr(meta, "image[0]/width", 16)
        self.check_attr(meta, "image[0]/height", 16)
        self.check_attr(meta, "image[0]/bits_per_pixel", 32)
        self.check_attr(meta, "image[0]/compression", "Uncompressed (RGB)")

    def test_au(self):
        meta = self.extract("audio_8khz_8bit_ulaw_4s39.au")
        self.check_attr(meta, "mime_type", "audio/basic")
        self.check_attr(meta, "nb_channel", 1)
        self.check_attr(meta, "bits_per_sample", 8)
        self.check_attr(meta, "bit_rate", 64096)
        self.check_attr(meta, "sample_rate", 8012)
        self.check_attr(meta, "compression", "8-bit ISDN u-law")
        self.check_attr(meta, "comment", "../tmp/temp.snd")
        self.check_attr(meta, "duration", timedelta(
            seconds=4, microseconds=391538))

    def test_xcf(self):
        meta = self.extract("cross.xcf")
        self.check_attr(meta, "comment", "Created with The GIMP")
        self.check_attr(meta, "width", 61)
        self.check_attr(meta, "height", 72)
        self.check_attr(meta, "compression", "RLE")
        self.check_attr(meta, "mime_type", "image/x-xcf")

    def test_tar(self):
        meta = self.extract("small_text.tar")
        self.check_attr(meta, "file[0]/filename", "dummy.txt")
        self.check_attr(meta, "file[0]/file_size", 62)
        self.check_attr(meta, "file[1]/file_attr", "-rwxr-xr-x (755)")
        self.check_attr(meta, "file[1]/last_modification",
                        datetime(2006, 10, 1, 13, 9, 3))
        self.check_attr(meta, "file[2]/file_type", "Normal disk file")

    def test_bmp(self):
        meta = self.extract("kde_haypo_corner.bmp")
        self.check_attr(meta, "width", 189)
        self.check_attr(meta, "nb_colors", 70)
        self.check_attr(meta, "compression", "Uncompressed")
        self.check_attr(meta, "mime_type", "image/x-ms-bmp")

    def test_avi(self):
        metadata = self.extract("smallville.s03e02.avi")
        self.check_attr(metadata, "duration", timedelta(
            minutes=44, seconds=1, microseconds=141141))
        self.check_attr(metadata, "producer",
                        "VirtualDubMod 1.5.10.1 (build 2366/release)")
        self.check_attr(metadata, "video/width", 640)
        self.check_attr(metadata, "video/height", 352)
        self.check_attr(metadata, "video/compression",
                        'XviD MPEG-4 (fourcc:"xvid")')
        self.check_attr(metadata, "video/frame_rate", 23.976)
        self.check_attr(metadata, "audio[1]/nb_channel", 2)
        self.check_attr(metadata, "audio[1]/sample_rate", 48000)
        self.check_attr(metadata, "audio[1]/compression", "MPEG Layer 3")

    def test_mp3_2(self):
        meta = self.extract("08lechat_hq_fr.mp3")
        self.check_attr(meta, "album", ["Arte Radio", "Chat Broodthaers"])
        self.check_attr(
            meta, "url", "Liens direct ARTE Radio: www.arteradio.com/son.html?473")
        self.check_attr(meta, "creation_date", date(2003, 1, 1))
        self.check_attr(meta, "producer", "www.arteradio.com")
        self.check_attr(meta, "sample_rate", 44100)
        self.check_attr(meta, "bit_rate", 128000)

    def test_jpeg(self):
        meta = self.extract("jpeg.exif.photoshop.jpg")
        self.check_attr(meta, "producer", ["Adobe Photoshop 7.0"])
        self.check_attr(meta, "width", 124)
        self.check_attr(meta, "compression", "JPEG (Progressive)")
        self.check_attr(meta, "creation_date",
                        datetime(2006, 6, 28, 14, 51, 9))

    def test_ogg_vorbis(self):
        meta = self.extract("interlude_david_aubrun.ogg")
        self.check_attr(meta, "title", "interlude symbiosys1")
        self.check_attr(meta, "artist", "david aubrun")
        self.check_attr(meta, "duration", timedelta(
            minutes=1, seconds=12, microseconds=19592))
        self.check_attr(meta, "audio[1]/nb_channel", 2)
        self.check_attr(meta, "audio[1]/format_version", "Vorbis version 0")
        self.check_attr(meta, "audio[1]/sample_rate", 44100)
        self.check_attr(meta, "mime_type", "audio/vorbis")

    def test_flv(self):
        meta = self.extract("breakdance.flv")
        self.check_attr(meta, "audio/sample_rate", 22050)
        self.check_attr(meta, "duration", timedelta(
            seconds=46, milliseconds=942))
        self.check_attr(meta, "producer", [
                        "YouTube, Inc.", "YouTube Metadata Injector."])

    def test_wmv(self):
        meta = self.extract("matrix_ping_pong.wmv")
        self.check_attr(meta, "title", "欽ちゃん＆香取慎吾の全日本仮装大賞")
        self.check_attr(meta, "duration", timedelta(
            minutes=1, seconds=43, milliseconds=900))
        self.check_attr(meta, "creation_date", datetime(
            2003, 6, 16, 7, 57, 23, 235000))
        self.check_attr(meta, "audio[1]/sample_rate", 8000)
        self.check_attr(meta, "audio[1]/bits_per_sample", 16)
        self.check_attr(meta, "audio[1]/compression",
                        "Windows Media Audio V7 / V8 / V9")
        self.check_attr(meta, "video[1]/width", 200)
        self.check_attr(meta, "video[1]/height", 150)
        self.check_attr(meta, "video[1]/bits_per_pixel", 24)

    def test_jpeg_2(self):
        meta = self.extract("usa_railroad.jpg")
        # Check IPTC parser
        self.check_attr(meta, "author", "Ian Britton")
        self.check_attr(meta, "copyright", "FreeFoto.com")
        self.check_attr(meta, "thumbnail_size", 4196),
        self.check_attr(meta, "iso_speed_ratings", 160),
        self.check_attr(meta, "exif_version", "0220"),
        self.check_attr(meta, "date_time_original", "2003:08:06 17:52:54"),
        self.check_attr(meta, "date_time_digitized", "2003:08:06 17:52:54"),
        self.check_attr(meta, "compressed_bits_per_pixel", 3.2),
        self.check_attr(meta, "aperture_value", 6),
        self.check_attr(meta, "exposure_bias_value", -0.5),
        self.check_attr(meta, "focal_length", 137),
        self.check_attr(meta, "flashpix_version", u"0100"),
        self.check_attr(meta, "focal_plane_x_resolution", 1322.0),
        self.check_attr(meta, "focal_plane_y_resolution", 1322.0),
        self.check_attr(meta, "focal_length_in_35mm_film", 205),

    def test_tga(self):
        meta = self.extract("hero.tga")
        self.check_attr(meta, "width", 320)
        self.check_attr(meta, "bits_per_pixel", 8)
        self.check_attr(meta, "nb_colors", 256)
        self.check_attr(meta, "compression", "8-bit uncompressed")

    def test_aifc(self):
        meta = self.extract("25min.aifc")
        self.check_attr(meta, "duration", timedelta(minutes=25, seconds=33))
        self.check_attr(meta, "nb_channel", 2)
        self.check_attr(meta, "sample_rate", 44100)
        self.check_attr(meta, "bit_rate", 1411200)
        self.check_attr(meta, "bits_per_sample", 16)
        self.check_attr(meta, "compression", "Little-endian, no compression")

    def test_wav_2(self):
        meta = self.extract("ladouce_1h15.wav")
        self.check_attr(meta, "duration", timedelta(
            hours=1, minutes=16, seconds=32, microseconds=516032))
        self.check_attr(meta, "nb_channel", 6)
        self.check_attr(meta, "sample_rate", 44100)
        self.check_attr(meta, "bits_per_sample", 32)
        self.check_attr(meta, "compression", "IEEE Float")
        self.check_attr(meta, "bit_rate", 8467200)

    def test_pcx(self):
        meta = self.extract("lara_croft.pcx")
        self.check_attr(meta, "width", 320)
        self.check_attr(meta, "nb_colors", 256)
        self.check_attr(meta, "compression", "Run-length encoding (RLE)")

    def test_sxw(self):
        meta = self.extract("hachoir.org.sxw")
        self.check_attr(meta, "mime_type", "application/vnd.sun.xml.writer")
        self.check_attr(meta, "file[0]/file_size", 30)
        self.check_attr(meta, "file[1]/creation_date",
                        datetime(2007, 1, 22, 19, 8, 14))
        self.check_attr(meta, "file[2]/filename",
                        "Configurations2/accelerator/current.xml")
        self.check_attr(meta, "file[2]/compression", "Deflate")

    def test_rm(self):
        meta = self.extract("firstrun.rm")
        self.check_attr(meta, "duration", timedelta(
            seconds=17, milliseconds=66))
        self.check_attr(meta, "creation_date",
                        datetime(2000, 6, 14, 10, 3, 18))
        self.check_attr(meta, "copyright", "©2000 RealNetworks")
        self.check_attr(meta, "producer",
                        "RealProducer Plus 6.1.0.153 Windows")
        self.check_attr(meta, "stream[0]/mime_type", "audio/x-pn-realaudio")
        self.check_attr(meta, "stream[0]/bit_rate", 32148)
        self.check_attr(meta, "stream[0]/title", "Audio Stream")
        self.check_attr(meta, "mime_type", "audio/x-pn-realaudio")
        self.check_attr(meta, "bit_rate", 32348)
        self.check_attr(meta, "stream[1]/bit_rate", 200)

    def test_ttf(self):
        meta = self.extract("deja_vu_serif-2.7.ttf")
        self.check_attr(meta, "title", "DejaVu Serif")
        self.check_attr(meta, "author", "DejaVu fonts team")
        self.check_attr(meta, "version", "2.7")
        self.check_attr(meta, "creation_date",
                        datetime(2006, 7, 6, 17, 29, 52))
        self.check_attr(meta, "last_modification",
                        datetime(2006, 7, 6, 17, 29, 52))
        self.check_attr(meta, "copyright", [
            "Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved.\nDejaVu changes are in public domain",
            "http://dejavu.sourceforge.net/wiki/index.php/License"])
        self.check_attr(meta, "url", "http://dejavu.sourceforge.net")
        self.check_attr(meta, "comment", [
            "Smallest readable size in pixels: 8 pixels",
            "Font direction: Mixed directional"])

    def test_exe_pe(self):
        meta = self.extract("twunk_16.exe")
        self.check_attr(meta, "title", [
            "Twain_32.dll Client's 16-Bit Thunking Server",
            "Twain Thunker"])
        self.check_attr(meta, "author", "Twain Working Group")
        self.check_attr(meta, "version", "1,7,0,0")
        self.check_attr(meta, "format_version",
                        "New-style executable: Dynamic-link library (DLL)")

    def test_torrent(self):
        meta = self.extract("debian-31r4-i386-binary-1.iso.torrent")
        self.check_attr(meta, "filename", "debian-31r4-i386-binary-1.iso")
        self.check_attr(
            meta, "url", "http://bttracker.acc.umu.se:6969/announce")
        self.check_attr(meta, "file_size", 669775872)
        self.check_attr(meta, "creation_date",
                        datetime(2006, 11, 16, 21, 44, 37))

    def test_jpeg_3(self):
        meta = self.extract("green_fire.jpg")
        self.check_attr(meta, 'height', 64)
        self.check_attr(meta, 'bits_per_pixel', 32)
        self.check_attr(
            meta, 'comment', ("Intel(R) JPEG Library, version 1,5,4,36", "JPEG quality: 80%"))

    def test_mp3_3(self):
        meta = self.extract("marc_kravetz.mp3")
        self.check_attr(meta, 'creation_date', datetime(
            2007, 7, 19, 9, 3, 57, tzinfo=createTimezone(2)))
        self.check_attr(meta, 'sample_rate', 48000)
        self.check_attr(meta, 'compr_rate', 12.0)
        self.check_attr(
            meta, 'album', "France Culture - Le portrait du jour par Marc Kravetz")
        self.check_attr(meta, 'author', "Marc Kravetz")
        self.check_attr(meta, 'duration', timedelta(0, 2, 400000))
        self.check_attr(meta, 'bit_rate', 128000)
        self.check_attr(meta, 'track_number', 32)
        self.check_attr(meta, 'bits_per_sample', 16)
        self.check_attr(meta, 'copyright', "Radio France")
        self.check_attr(meta, 'format_version', "MPEG version 1 layer III")

    def test_mov(self):
        meta = self.extract("pentax_320x240.mov")
        self.check_attr(meta, 'width', 320)
        self.check_attr(meta, 'height', 240)
        self.check_attr(meta, 'duration', timedelta(0, 4, 966667))
        self.check_attr(meta, 'creation_date',
                        datetime(2005, 8, 11, 14, 3, 54))
        self.check_attr(meta, 'last_modification',
                        datetime(2005, 8, 11, 14, 3, 54))

    def test_jpeg_gps(self):
        meta = self.extract("gps.jpg")
        self.check_attr(meta, 'altitude', 78.0)
        self.check_attr(meta, 'creation_date',
                        datetime(2003, 5, 24, 22, 29, 14))
        self.check_attr(meta, 'latitude', 35.616019444444447)
        self.check_attr(meta, 'longitude', 139.69731666666667)
        self.check_attr(meta, 'camera_model', 'A5301T')
        self.check_attr(meta, 'camera_manufacturer', 'KDDI-TS')

    def test_ani(self):
        meta = self.extract("angle-bear-48x48.ani")
        self.check_attr(meta, 'title', "Angel Bear")
        self.check_attr(
            meta, 'artist', "Copyright ©Loraine Wauer-Ferus http://www.billybear4kids.com")
        self.check_attr(meta, 'frame_rate', 4.0)

    def test_flac(self):
        meta = self.extract("hotel_california.flac")
        self.check_attr(meta, 'title', "Hotel California")
        self.check_attr(meta, 'artist', "The Eagles")
        self.check_attr(meta, 'duration', timedelta(
            seconds=51, microseconds=512834))
        self.check_attr(meta, 'nb_channel', 2)
        self.check_attr(meta, 'sample_rate', 44100)
        self.check_attr(meta, 'bits_per_sample', 16)
        self.check_attr(meta, 'producer', 'reference libFLAC 1.1.2 20050205')

    def test_doc(self):
        meta = self.extract("radpoor.doc")
        self.check_attr(meta, 'title', "\u062a\u0633\u062a")
        self.check_attr(meta, 'author', 'Soroosh Radpoor')
        self.check_attr(meta, 'creation_date', datetime(2008, 9, 2, 16, 8, 30))

    def test_mpeg4(self):
        meta = self.extract("quicktime.mp4")
        self.check_attr(meta, 'width', 190)
        self.check_attr(meta, 'height', 240)
        self.check_attr(meta, 'creation_date',
                        datetime(2005, 10, 28, 17, 46, 46))
        self.check_attr(meta, 'mime_type', 'video/mp4')

    def test_tiff(self):
        meta = self.extract("sample.tif")
        self.check_attr(meta, 'width', 1600)
        self.check_attr(meta, 'height', 2100)
        self.check_attr(meta, 'width_dpi', 200)
        self.check_attr(meta, 'height_dpi', 200)
        self.check_attr(meta, 'producer', 'mieconvert')

    def test_cr2(self):
        meta = self.extract("canon.raw.cr2")
        self.check_attr(meta, 'width', 5184)
        self.check_attr(meta, 'height', 3456)
        self.check_attr(meta, 'creation_date',
                        datetime(2015, 11, 15, 13, 35, 29))
        self.check_attr(meta, 'date_time_original',
                        datetime(2015, 11, 15, 13, 35, 29))
        self.check_attr(meta, 'camera_manufacturer', 'Canon')
        self.check_attr(meta, 'camera_model', 'Canon EOS REBEL T5i')


class TestMetadataCommandLine(unittest.TestCase):

    def test_metadata(self):
        filename = os.path.join(DATADIR, 'gps.jpg')
        args = [sys.executable, PROGRAM, filename]
        proc = subprocess.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout, _ = proc.communicate()
        stdout = stdout.decode('ascii', 'replace').strip()
        self.assertEqual(stdout, """Metadata:
- Title: 030524_2221~01
- Image width: 144 pixels
- Image height: 176 pixels
- Image orientation: Horizontal (normal)
- Bits/pixel: 24
- Pixel format: YCbCr
- Creation date: 2003-05-24 22:29:14
- Latitude: 35.61601944444445
- Longitude: 139.69731666666667
- Altitude: 78.0 meters
- Camera model: A5301T
- Camera manufacturer: KDDI-TS
- Compression: JPEG (Baseline)
- EXIF version: 0220
- Date-time original: 2003-05-24 22:21:01
- Flashpix version: 0100
- Comment: JPEG quality: 90%
- MIME type: image/jpeg
- Endianness: Big endian""")


if __name__ == "__main__":
    setup_tests()
    unittest.main()
