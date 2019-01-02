#!/usr/bin/env python3
"""
Test hachoir-parser using the testcase.
"""

from hachoir.core.error import error
from hachoir.stream import StringInputStream
from hachoir.parser import createParser, HachoirParserList, ValidateError
from hachoir.test import setup_tests
from array import array
from datetime import datetime
import random
import os
import sys
import unittest

DATADIR = os.path.join(os.path.dirname(__file__), 'files')


class TestParsers(unittest.TestCase):
    verbose = False

    def parse(self, filename):
        if self.verbose:
            print("[+] Test %s:" % filename)
            sys.stdout.write("  - Create parser: ")
            sys.stdout.flush()

        fullname = os.path.join(DATADIR, filename)
        parser = createParser(fullname)
        if not parser:
            self.fail("unable to create parser")
        self.addCleanup(parser.close)

        if self.verbose:
            sys.stdout.write("ok\n")
        return parser

    def checkValue(self, parser, path, value):
        if self.verbose:
            sys.stdout.write("  - Check field %s.value=%s (%s): "
                             % (path, repr(value), value.__class__.__name__))
            sys.stdout.flush()
        read = parser[path].value
        self.assertEqual(read, value,
                         "wrong value (%s, %s)"
                         % (repr(read), read.__class__.__name__))

    def checkDisplay(self, parser, path, value):
        if self.verbose:
            sys.stdout.write("  - Check field %s.display=%s (%s): "
                             % (path, repr(value), value.__class__.__name__))
            sys.stdout.flush()
        read = parser[path].display
        self.assertEqual(read, value,
                         "wrong value (%s, %s)"
                         % (repr(read), read.__class__.__name__))

    def checkDesc(self, parser, path, value):
        if self.verbose:
            sys.stdout.write("  - Check field %s.description=%s (%s): "
                             % (path, repr(value), value.__class__.__name__))
            sys.stdout.flush()
        read = parser[path].description
        self.assertEqual(read, value,
                         "wrong value (%s, %s)"
                         % (repr(read), read.__class__.__name__))

    def checkNames(self, parser, path, names):
        if self.verbose:
            sys.stdout.write("  - Check field names %s=(%s) (%u): "
                             % (path, ", ".join(names), len(names)))
            sys.stdout.flush()
        fieldset = parser[path]
        if len(fieldset) != len(names):
            self.fail("invalid length (%u)" % len(fieldset))
        names = list(names)
        read = list(field.name for field in fieldset)
        self.assertEqual(names, read,
                         "wrong names (%s)" % ", ".join(read))

    def test_3ds(self):
        parser = self.parse("yellowdude.3ds")
        self.checkValue(parser, "/main/version/version", 2)
        self.checkNames(parser, "/main",
                        ("type", "size", "version", "obj_mat"))

    def test_png(self):
        parser = self.parse("logo-kubuntu.png")
        self.checkValue(parser, "/header/width", 331)
        self.checkValue(parser, "/time/second", 46)

    def test_wav(self):
        parser = self.parse("kde_click.wav")
        self.checkValue(parser, "/info/producer/text", "Sound Forge 4.5")
        self.checkValue(parser, "/format/sample_per_sec", 22050)

    def test_mbr(self):
        parser = self.parse("mbr_linux_and_ext")
        self.checkValue(parser, "/mbr/header[1]/size", 65545200)
        self.checkDisplay(parser, "/mbr/signature", "0xaa55")

    def test_mkv(self):
        parser = self.parse("flashmob.mkv")
        self.checkValue(parser, "/Segment[0]/Cues/CuePoint[1]/CueTrackPositions[0]"
                        + "/CueClusterPosition/cluster/BlockGroup[14]/Block/block/timecode", 422)
        self.checkValue(parser, "/Segment[0]/Tags[0]/Tag[0]/SimpleTag[3]/TagString/unicode",
                        "\xa9 dadaprod, licence Creative Commons by-nc-sa 2.0 fr")

    def test_mkv2(self):
        parser = self.parse("10min.mkv")
        self.checkValue(parser, "/Segment[0]/size", None)
        self.checkValue(
            parser, "/Segment[0]/Tracks[0]/TrackEntry[0]/CodecID/string", "V_MPEG4/ISO/AVC")

    def test_ico(self):
        parser = self.parse("wormux_32x32_16c.ico")
        self.checkValue(parser, "icon_header[0]/height", 16)
        self.checkValue(parser, "icon_data[0]/header/hdr_size", 40)

    def test_cda(self):
        parser = self.parse("cd_0008_5C48_1m53s.cda")
        self.checkValue(parser, "filesize", 36)
        self.checkValue(parser, "/cdda/track_no", 4)
        self.checkDisplay(parser, "/cdda/disc_serial", "0008-5C48")
        self.checkValue(parser, "/cdda/rb_length/second", 53)

    def test_mp3(self):
        parser = self.parse("sheep_on_drugs.mp3")
        self.checkValue(parser, "/id3v2/field[6]/content/text",
                        'Stainless Steel Provider is compilated to the car of Twinstar.')
        self.checkValue(parser, "/frames/frame[0]/use_padding", False)

    def test_au(self):
        parser = self.parse("audio_8khz_8bit_ulaw_4s39.au")
        self.checkValue(parser, "info", "../tmp/temp.snd")
        self.checkDisplay(parser, "codec", "8-bit ISDN u-law")

    def test_gzip(self):
        parser = self.parse("test.txt.gz")
        self.checkValue(parser, "filename", "test.txt")

    def test_mp3_steganography(self):
        parser = self.parse("steganography.mp3")
        self.checkValue(parser, "/frames/padding[0]", b"misc est un canard\r")
        self.checkDesc(parser, "/frames", 'Frames: Variable bit rate (VBR)')
        self.checkDesc(
            parser, "/frames/frame[1]", 'MPEG-1 layer III, 160.0 Kbit/sec, 44.1 kHz')

    def test_rpm(self):
        parser = self.parse("ftp-0.17-537.i586.rpm")
        self.checkValue(parser, "name", "ftp-0.17-537")
        self.checkValue(parser, "os", 1)
        self.checkValue(parser, "checksum/content_item[2]/value", 50823)
        self.checkValue(
            parser, "header/content_item[15]/value", "ftp://ftp.uk.linux.org/pub/linux/Networking/netkit")

    def test_jpeg(self):
        parser = self.parse("jpeg.exif.photoshop.jpg")
        self.checkValue(parser, "app0/content/jfif", "JFIF\x00")
        self.checkValue(parser, "app0/content/ver_maj", 1)
        self.checkValue(parser, "photoshop/content/signature", "Photoshop 3.0")
        self.checkValue(parser, "photoshop/content/copyright_flag/content", 0)
        self.checkValue(parser, "exif/content/header", "Exif\0\0")
        self.checkValue(parser, "exif/content/version", 42)

    def test_tar(self):
        parser = self.parse("small_text.tar")
        self.checkDisplay(parser, "file[0]/name", '"dummy.txt"')
        self.checkDisplay(parser, "file[1]/mode", '"0000755"')
        self.checkDisplay(parser, "file[1]/type", 'Directory')
        self.checkDisplay(parser, "file[2]/devmajor", '(empty)')

    def test_rar(self):
        parser = self.parse("hachoir-core.rar")
        self.checkValue(parser, "archive_start/crc16", 0x77E1)
        self.checkValue(parser, "new_sub_block[0]/crc16", 0x2994)
        self.checkValue(parser, "file[0]/crc32", 0x4C6D13ED)
        self.checkValue(parser, "new_sub_block[1]/crc32", 0x34528E23)
        self.checkValue(parser, "file[1]/filename",
                        r".svn\prop-base\README.svn-base")
        self.checkValue(parser, "new_sub_block[1]/filename", 'ACL')
        # archive_end bad candidate for checking
        self.checkValue(parser, "new_sub_block[362]/crc32", 0x6C84C95E)

    def test_ace(self):
        parser = self.parse("hachoir-core.ace")
        self.checkValue(parser, "header/crc16", 0xA9BE)
        self.checkValue(parser, "file[0]/reserved", 0x4554)
        self.checkValue(parser, "file[1]/filename", r"hachoir_core\.svn")
        self.checkValue(parser, "file[2]/parameters", 0x000A)
        # End of archive, lots of work...
        # self.checkValue(parser, "new_recovery[0]/signature", "**ACE**")

    def test_bmp(self):
        parser = self.parse("kde_haypo_corner.bmp")
        self.checkValue(parser, "header/width", 189)
        self.checkValue(parser, "header/used_colors", 70)
        self.checkDesc(
            parser, "palette/color[1]", "RGB color: White (opacity: 0%)")
        self.checkValue(parser, "pixels/line[26]/pixel[14]", 28)

    def test_der(self):
        parser = self.parse("cacert_class3.der")
        self.checkDisplay(parser, "seq[0]/class", 'universal')
        self.checkDesc(parser, "seq[0]/seq[0]/seq[1]/obj_id[0]",
                       "Object identifier: 1.2.840.113549.1.1.4")
        self.checkValue(
            parser, "seq[0]/seq[0]/seq[2]/set[0]/seq[0]/print_str[0]/value", "Root CA")
        self.checkValue(
            parser, "seq[0]/seq[0]/seq[2]/set[3]/seq[0]/ia5_str[0]/value", "support@cacert.org")
        self.checkValue(parser, "seq[0]/bit_str[0]/size", 513)

    def check_pyc(self, parser):
        self.checkValue(parser, "/content/consts/item[0]", 42)
        self.checkValue(parser, "/content/stack_size", 4)
        self.checkValue(
            parser, "/content/consts/item[1]", 2535301200456458802993406410752)
        self.checkValue(parser, "/content/consts/item[4]", 0.3j)
        self.checkValue(parser, "/content/consts/item[8]", b"abc")
        self.checkValue(parser, "/content/filename", b"pyc_example.py")

    def test_pyc_1_5(self):
        parser = self.parse("pyc_example_1.5.2_pyc.bin")
        self.check_pyc(parser)

    def test_pyc_2_2(self):
        parser = self.parse("pyc_example_2.2.3_pyc.bin")
        self.check_pyc(parser)

    def test_pyc_2_5(self):
        parser = self.parse("pyc_example_2.5c1_pyc.bin")
        self.check_pyc(parser)

    def check_pyc_37(self, parser):
        parser = self.parse("python.cpython-37.pyc.bin")
        self.checkValue(parser, "/content/consts/item[0]/name/text", "f")

    def test_java(self):
        parser = self.parse("ReferenceMap.class")
        self.checkValue(parser, "/minor_version", 3)
        self.checkValue(parser, "/major_version", 45)
        self.checkValue(parser, "/constant_pool_count", 326)
        self.checkValue(
            parser, "/constant_pool/constant_pool[324]/bytes", "([Ljava/lang/Object;Ljava/lang/Object;)V")
        self.checkValue(parser, "/super_class", 80)
        self.checkValue(parser, "/interfaces_count", 0)
        self.checkValue(parser, "/fields_count", 16)
        self.checkValue(
            parser, "/fields/fields[3]/attributes/attributes[0]/attribute_name_index", 93)
        self.checkValue(parser, "/methods_count", 31)
        self.checkValue(
            parser, "/methods/methods[30]/attributes/attributes[0]/code_length", 5)
        self.checkValue(parser, "/attributes_count", 3)
        self.checkValue(
            parser, "/attributes/attributes[2]/classes/classes[1]/inner_name_index", 83)

    def test_swf(self):
        parser = self.parse("claque-beignet.swf")
        self.checkDesc(parser, "rect", "Rectangle: 550x400")
        self.checkDisplay(parser, "frame_rate", "24.0")
        self.checkDesc(parser, "bkgd_color[0]/color", "RGB color: #CC9933")
        self.checkDisplay(parser, "def_sound[0]/rate", "11.0 kHz")
        self.checkValue(parser, "def_sound[0]/len", 1661)
        self.checkValue(parser, "sound_hdr2[0]/sound_is_16bit", False)
        self.checkValue(parser, "export[0]/export[0]/name", "C bras")

    def test_flv(self):
        parser = self.parse("breakdance.flv")
        self.checkDisplay(parser, "/audio[0]/codec", "MP3")
        self.checkValue(parser, "/audio[2]/timestamp", 52)
        self.checkDisplay(parser, "/video[0]/codec", "Sorensen H.263")
        self.checkValue(
            parser, "/metadata/entry[1]/item[8]/attr[1]/item[4]/value/exponent", 20)

    def test_tcpdump(self):
        parser = self.parse("arp_dns_ping_dns.tcpdump")
        self.checkValue(parser, "/packet[5]/ipv4/ttl", 120)
        self.checkDisplay(parser, "/packet[3]/ts_epoch", "2006-11-23 23:13:19")
        self.checkValue(parser, "/packet[3]/ipv4/src", "212.27.54.252")
        self.checkDisplay(parser, "/packet[7]/udp/src", "DNS")

    def test_ext2(self):
        parser = self.parse("my60k.ext2")
        self.checkDisplay(parser, "/superblock/last_check",
                          '2006-12-04 22:56:37')
        self.checkDisplay(parser, "/superblock/creator_os", "Linux")
        self.checkDisplay(parser, "/superblock/errors", "Continue")
        self.checkValue(parser, "/group_desc/group[0]/block_bitmap", 3)
        self.checkValue(parser, "/group_desc/group[0]/free_blocks_count", 44)
        self.checkValue(parser, "/group[0]/block_bitmap/item[9]", False)
        self.checkDisplay(
            parser, "/group[0]/inode_table/inode[1]/mode/file_type", "Directory")
        self.checkDesc(parser, "/group[0]/inode_table/inode[10]",
                       "Inode 11: Directory, size=1024 bytes, mode=drwxr-xr-x")
        self.checkValue(parser, "/group[0]/inode_table/inode[11]/size", 1816)
        self.checkDisplay(
            parser, "/group[0]/inode_table/inode[11]/ctime", '2006-12-04 23:22:00')
        self.checkValue(
            parser, "/superblock/feature_compat/dir_prealloc", False)
        self.checkValue(
            parser, "/superblock/feature_compat/imagic_inodes", False)
        self.checkValue(
            parser, "/superblock/feature_compat/has_journal", False)
        self.checkValue(parser, "/superblock/feature_compat/ext_attr", False)
        self.checkValue(parser, "/superblock/feature_compat/resize_inode", True)
        self.checkValue(parser, "/superblock/feature_compat/dir_index", True)
        self.checkValue(
            parser, "/superblock/feature_incompat/compression", False)
        self.checkValue(parser, "/superblock/feature_incompat/filetype", True)
        self.checkValue(parser, "/superblock/feature_incompat/recover", False)
        self.checkValue(
            parser, "/superblock/feature_incompat/journal_dev", False)
        self.checkValue(parser, "/superblock/feature_incompat/meta_bg", False)
        self.checkValue(
            parser, "/superblock/feature_ro_compat/sparse_super", True)
        self.checkValue(
            parser, "/superblock/feature_ro_compat/large_file", False)
        self.checkValue(
            parser, "/superblock/feature_ro_compat/btree_dir", False)
        self.checkValue(parser, "/superblock/feature_incompat/filetype", True)
        self.checkValue(parser, "/superblock/feature_incompat/recover", False)
        self.checkDisplay(parser, "/superblock/def_hash_version", "TEA")
        self.checkValue(
            parser, "/group[0]/inode_table/inode[0]/flags/secrm", False)
        self.checkDisplay(parser, "/superblock/rev_level",
                          "V2 format w/ dynamic inode sizes")

    def test_ext2_default_mount_opts(self):
        parser = self.parse("default_mount_opts.ext2")
        self.checkValue(parser, "/superblock/default_mount_opts/debug", False)
        self.checkValue(
            parser, "/superblock/default_mount_opts/bsdgroups", False)
        self.checkValue(
            parser, "/superblock/default_mount_opts/xattr_user", True)
        self.checkValue(parser, "/superblock/default_mount_opts/acl", True)
        self.checkValue(parser, "/superblock/default_mount_opts/uid16", False)
        self.checkDisplay(parser, "/superblock/default_mount_opts/jmode", "none")

    def test_ext2_variety_inode_types(self):
        parser = self.parse("types.ext2")
        self.checkDesc(parser, "/group[0]/inode_table/inode[12]",
                       "Inode 13: Symbolic link (-> XYZ), size=3 bytes, mode=lrwxrwxrwx")

    def test_bmp2(self):
        parser = self.parse("article01.bmp")
        self.checkDisplay(parser, "/header/red_mask", '0x00ff0000')
        self.checkDisplay(parser, "/header/color_space",
                          "Business (Saturation)")
        self.checkValue(parser, "/pixels/line[94]/pixel[11]", 15265520)

    def test_reiserfs3(self):
        parser = self.parse("reiserfs_v3_332k.bin")
        self.checkValue(parser, "/superblock/root_block", 645)
        self.checkDisplay(parser, "/superblock/hash_function", "R5_HASH")
        self.checkValue(parser, "/superblock/tree_height", 3)

    def test_pcx(self):
        parser = self.parse("lara_croft.pcx")
        self.checkDesc(parser, "/palette_4bits/color[8]", "RGB color: #100000")
        self.checkDesc(parser, "/palette_8bits/color[0]", "RGB color: Black")
        self.checkValue(parser, "/compression", 1)
        self.checkValue(parser, "/horiz_dpi", 500)

    def test_linux_swap(self):
        parser = self.parse("linux_swap_9pages")
        self.checkValue(parser, "/version", 1)
        self.checkValue(parser, "/last_page", 9)
        self.checkValue(parser, "/magic", "SWAPSPACE2")

    def test_wmf(self):
        parser = self.parse("pikachu.wmf")
        self.checkValue(parser, "/max_record_size", 510)
        self.checkValue(parser, "/func[2]/y", 10094)
        self.checkDisplay(parser, "/func[4]/brush_style", "Solid")
        self.checkValue(parser, "/func[10]/object_id", 2)

    def test_wmf2(self):
        parser = self.parse("globe.wmf")
        self.checkValue(parser, "/file_size", 3923)
        self.checkValue(parser, "/func[1]/x", 9989)
        self.checkDisplay(parser, "/func[4]/operation", "Copy pen (P)")
        self.checkDisplay(parser, "/func[9]/brush_style", "Null")

    def test_midi(self):
        parser = self.parse("indiana.mid")
        self.checkDesc(parser, "/header",
                       "Multiple tracks, synchronous; 3 tracks")
        self.checkDisplay(
            parser, "/track[0]/command[1]/microsec_quarter", "300.00 ms")
        self.checkDisplay(parser, "/track[1]/command[6]/note", "A (octave 5)")
        self.checkValue(parser, "/track[1]/command[8]/time", 408)
        self.checkValue(parser, "/track[1]/command[8]/velocity", 80)

    def test_wmf_emf(self):
        parser = self.parse("grasslogo_vector.emf")
        self.checkValue(parser, "/func[4]/y", 297)
        self.checkDesc(parser, "/func[15]", "Begin path")
        self.checkDesc(parser, "/func[40]/color",
                       "RGB color: #008F00 (opacity: 0%)")
        self.checkValue(parser, "/emf_header/maj_ver", 1)
        self.checkValue(parser, "/emf_header/width_px", 1024)
        self.checkValue(parser, "/emf_header/width_mm", 270)
        self.checkValue(parser, "/emf_header/description",
                        "Adobe Illustrator EMF 8.0")

    def test_gif(self):
        parser = self.parse("india_map.gif")
        self.checkValue(parser, "/screen/global_map", True)
        self.checkDesc(parser, "/color_map/color[0]", "RGB color: Black")
        self.checkValue(parser, "/image[0]/height", 794)

    def test_exe_msdos(self):
        parser = self.parse("cercle.exe")
        self.checkValue(parser, "/msdos/reloc_offset", 28)
        self.checkDisplay(parser, "/msdos/init_cs_ip", "0x00000315")

    def test_exe_pe(self):
        parser = self.parse("eula.exe")
        self.checkDisplay(parser, "/pe_header/cpu", "Intel 80386")
        self.checkDisplay(parser, "/pe_opt_header/subsystem", "Windows GUI")
        self.checkDisplay(parser, "/pe_opt_header/import/rva", "0x00008314")
        self.checkDisplay(parser, "/section_hdr[1]/mem_size", "4632 bytes")
        self.checkValue(parser, "/section_hdr[1]/is_readable", True)
        self.checkValue(parser, "/section_hdr[1]/is_executable", False)
        self.checkValue(
            parser, "/section_rsrc/version_info/node[0]/node[1]/node[0]/node[0]/value", "Dell Inc")
        self.checkDesc(
            parser, "/section_rsrc/icon[0]/bmp_header", "Bitmap info header: 16x32 pixels, 4 bits/pixel")
        self.checkDesc(
            parser, "/section_rsrc/icon[1]", "Resource #296 content: type=3")

    def test_laf(self):
        parser = self.parse("ocr10.laf")
        self.checkValue(parser, "/chars/char[3]/data_offset", 201)
        self.checkValue(parser, "/chars/char[8]/width_pixels", 10)

    def test_laf2(self):
        parser = self.parse("kino14s.laf")
        self.checkValue(parser, "/max_char_width", 26)
        self.checkValue(parser, "/char_codes/char[5]", 5)
        self.checkValue(parser, "/chars/char[1]/data_offset", 1)
        self.checkValue(parser, "/chars/char[1]/height_pixels", 13)
        self.checkValue(
            parser, "/char_data/char_bitmap[3]/line[1]/pixel[0]", 128)

    def test_bz2(self):
        parser = self.parse("free-software-song.midi.bz2")
        self.checkDisplay(parser, "/blocksize", "'9'")
        self.checkDisplay(parser, "/file/crc32", "0x8c3c1b7b")

    def test_elf_program_32lsb(self):
        parser = self.parse("ping_20020927-3ubuntu2")
        self.checkDisplay(parser, "/header/class", "32 bits")
        self.checkDisplay(parser, "/header/endian", "Little endian")
        self.checkDisplay(parser, "/header/type", "Executable file")
        self.checkDisplay(parser, "/header/machine", "Intel 80386")
        self.checkValue(parser, "/header/phentsize", 32)
        self.checkDisplay(parser, "/prg_header[1]/type", "Program interpreter")
        self.checkValue(
            parser, "/section_header[0]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_alloc", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[1]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[10]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[10]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[10]/flags/is_exec", True)
        self.checkValue(
            parser, "/section_header[10]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[17]/flags/is_writable", True)
        self.checkValue(
            parser, "/section_header[17]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[17]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[17]/flags/is_tls", False)

    def test_elf_program_64lsb(self):
        parser = self.parse("get-versions.64bit.little.elf")
        self.checkDisplay(parser, "/header/endian", "Little endian")
        self.checkDisplay(parser, "/header/type", "Executable file")
        self.checkDisplay(parser, "/header/machine", "Advanced Micro Devices x86-64")
        self.checkValue(parser, "/header/phentsize", 56)
        self.checkDisplay(parser, "/prg_header[1]/type", "Program interpreter")
        self.checkValue(
            parser, "/section_header[0]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_alloc", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[1]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[10]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[10]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[10]/flags/is_exec", True)
        self.checkValue(
            parser, "/section_header[10]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[18]/flags/is_writable", True)
        self.checkValue(
            parser, "/section_header[18]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[18]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[18]/flags/is_tls", False)

    def test_elf_program_32msb(self):
        parser = self.parse("mev.32bit.big.elf")
        self.checkDisplay(parser, "/header/class", "32 bits")
        self.checkDisplay(parser, "/header/endian", "Big endian")
        self.checkDisplay(parser, "/header/type", "Shared object file")
        self.checkDisplay(parser, "/header/machine", "MIPS I Architecture")
        self.checkValue(parser, "/header/phentsize", 32)
        self.checkDisplay(parser, "/prg_header[1]/type", "Program interpreter")
        self.checkValue(
            parser, "/section_header[0]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_alloc", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[1]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[13]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[13]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[13]/flags/is_exec", True)
        self.checkValue(
            parser, "/section_header[13]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[19]/flags/is_writable", True)
        self.checkValue(
            parser, "/section_header[19]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[19]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[19]/flags/is_tls", False)

    def test_elf_program_64msb(self):
        parser = self.parse("mev.64bit.big.elf")
        self.checkDisplay(parser, "/header/class", "64 bits")
        self.checkDisplay(parser, "/header/endian", "Big endian")
        self.checkDisplay(parser, "/header/type", "Shared object file")
        self.checkDisplay(parser, "/header/machine", "IBM S390")
        self.checkValue(parser, "/header/phentsize", 56)
        self.checkDisplay(parser, "/prg_header[1]/type", "Program interpreter")
        self.checkValue(
            parser, "/section_header[0]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_alloc", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[0]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[1]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[1]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[13]/flags/is_writable", False)
        self.checkValue(
            parser, "/section_header[13]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[13]/flags/is_exec", True)
        self.checkValue(
            parser, "/section_header[13]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[19]/flags/is_writable", True)
        self.checkValue(
            parser, "/section_header[19]/flags/is_alloc", True)
        self.checkValue(
            parser, "/section_header[19]/flags/is_exec", False)
        self.checkValue(
            parser, "/section_header[19]/flags/is_tls", False)
        self.checkValue(
            parser, "/section_header[10]/flags/is_info_link", True)

    def test_cab(self):
        parser = self.parse("georgia.cab")
        self.checkDisplay(parser, "/minor_version", "3")
        self.checkDisplay(parser, "/major_version", "1")
        self.checkDesc(parser, "/file[0]", 'File "fontinst.inf" (64 bytes)')
        self.checkValue(parser, "/file[1]/filename", "Georgiaz.TTF")

    def test_torrent(self):
        parser = self.parse("debian-31r4-i386-binary-1.iso.torrent")
        self.checkValue(parser, "/root/announce",
                        "http://bttracker.acc.umu.se:6969/announce")
        self.checkValue(parser, "/root/comment",
                        '"Debian CD from cdimage.debian.org"')
        self.checkDisplay(parser, "/root/creation_date", '2006-11-16 21:44:37')
        self.checkDisplay(parser, "/root/info/value/length", "638.7 MB")
        self.checkDisplay(parser, "/root/info/value/piece_length", "512.0 KB")

    def test_fat16(self):
        parser = self.parse("dell8.fat16")
        self.checkValue(parser, "/boot/oem_name", "Dell 8.0")
        self.checkDisplay(parser, "/boot/serial", "0x07d6090d")
        self.checkValue(parser, "/boot/label", "DellUtility")
        self.checkValue(parser, "/boot/fs_type", "FAT16")
        self.checkValue(parser, "/fat[1]/entry[2]", 3)
        self.checkDisplay(parser, "/fat[0]/entry[4008]", "free cluster")
        self.checkDesc(parser, "/root[0]/entry[0]",
                       "Long filename part: 'command.com' [65]")
        self.checkDesc(parser, "/root[0]/entry[1]", "File: 'COMMAND.COM'")
        self.checkValue(parser, "/root[0]/entry[2]/hidden", True)
        self.checkDesc(
            parser, "/root[0]/entry[2]/create", "2006-09-13 15:01:16")
        self.checkDesc(parser, "/root[0]/entry[2]/access", "2006-09-13")
        self.checkDesc(
            parser, "/root[0]/entry[2]/modify", "2005-07-26 00:48:26")
        self.checkValue(parser, "/root[0]/entry[2]/size", 29690)

    def test_xm(self):
        parser = self.parse("dontyou.xm")
        self.checkValue(parser, "/header/title", "Dont you... voguemix")
        self.checkValue(parser, "/header/bpm", 128)
        self.checkValue(parser, "/pattern[0]/data_size", 708)
        self.checkDisplay(
            parser, "/pattern[0]/row[0]/note[0]/note", "F (octave 5)")
        self.checkValue(
            parser, "/pattern[0]/row[0]/note[0]/effect_parameter", 0x0A)
        self.checkDisplay(
            parser, "/pattern[0]/row[0]/note[1]/note", "A (octave 5)")
        self.checkValue(
            parser, "/pattern[0]/row[0]/note[1]/effect_parameter", 0x80)
        self.checkValue(parser, "/pattern[20]/data_size", 1129)
        self.checkDisplay(
            parser, "/pattern[20]/row[0]/note[0]/note", "C# (octave 5)")
        self.checkValue(parser, "/pattern[20]/row[0]/note[0]/instrument", 5)
        self.checkValue(parser, "/instrument[3]/name", "Vogue of Triton")
        self.checkValue(
            parser, "/instrument[4]/second_header/panning_points", 6)
        self.checkValue(parser, "/instrument[20]/name", "808-hi5.smp")

    def test_s3m(self):
        parser = self.parse("satellite_one.s3m")
        self.checkValue(parser, "/header/title", "Satellite one.")
        self.checkValue(parser, "/instrument[0]/sample_offset", 27024)
        self.checkValue(parser, "/instrument[0]/c4_speed", 8363)
        self.checkValue(parser, "/instrument[0]/name", "By Purple Motion of")
        self.checkValue(parser, "/instrument[1]/name", "Future Crew - 1993")
        self.checkValue(parser, "/pattern[0]/row[0]/note[0]/volume", 54)

    def test_ptm(self):
        parser = self.parse("anti-arpeggio_tune.ptm")
        self.checkValue(parser, "/header/title", "Anti-arpeggio tune!-VV/AcMe")
        self.checkValue(parser, "/instrument[0]/sample_offset", 30928)
        self.checkValue(parser, "/instrument[0]/c4_speed", 8363)
        self.checkValue(parser, "/instrument[0]/name", "Yep guess wat....")
        self.checkValue(
            parser, "/instrument[1]/name", "Mag ik even mijn ongenoegen")
        self.checkValue(parser, "/instrument[1]/gus_loop_flags", 0)
        self.checkValue(parser, "/pattern[0]/row[0]/note[0]/effect", 15)

    def test_lnk(self):
        parser = self.parse("vim.lnk")
        self.checkValue(parser, "/creation_time",
                        datetime(2006, 5, 7, 14, 18, 32))
        self.checkValue(parser, "/target_filesize", 1363968)

    def test_chm(self):
        parser = self.parse("7zip.chm")
        self.checkValue(parser, "/itsf/version", 3)
        self.checkDisplay(parser, "/itsf/lang_id", "Russian")
        self.checkValue(parser, "/itsf/dir_uuid/time",
                        datetime(1997, 1, 31, 20, 42, 14, 890626))
        self.checkDisplay(parser, "/itsf/stream_uuid/variant",
                          "Microsoft Corporation")
        self.checkDisplay(parser, "/itsf/stream_uuid/mac",
                          'INTEL CORPORATION - HF1-06 [22:e6:ec]')
        self.checkDisplay(parser, "/file_size/file_size", "75.6 KB")
        self.checkDisplay(parser, "/dir/itsp/lang_id", "English United States")
        self.checkValue(parser, "/dir/pmgl[0]/entry[1]/name", "/#IDXHDR")

    def test_blp(self):
        parser = self.parse("swat.blp")
        self.checkValue(parser, "flags", 8)
        self.checkValue(parser, "height", 256)
        self.checkValue(parser, "width", 256)
        self.checkValue(parser, "jpeg_header_len", 10)

    def test_nds(self):
        parser = self.parse("nitrodir.nds")
        self.checkValue(parser, "/header/game_title", '.')
        self.checkValue(parser, "/header/header_crc16", 29398)
        self.checkValue(parser, "/banner/icon_data/tile[3,3]/pixel[7,6]", 5)
        self.checkValue(parser, "/banner/palette_color[13]/blue", 28)
        self.checkValue(
            parser, "/filename_table/directory[3]/entry[1]/name", "subsubdir1")
        self.checkValue(
            parser, "/filename_table/directory[3]/entry[1]/dir_id", 61444)
        self.checkValue(
            parser, "/filename_table/directory[4]/entry[0]/name", "file2.txt")
        self.checkValue(
            parser, "/filename_table/directory[4]/entry[0]/is_directory", False)
        self.checkValue(parser, "/file[1]", b"Hello from file2.txt\n\n")

    def test_prs_pak(self):
        parser = self.parse("paktest.pak")
        self.checkValue(
            parser, "/file[0]/filename", "hachoir/png_331x90x8_truncated.png")
        self.checkValue(parser, "/file[0]/size", 100)
        self.checkValue(
            parser, "/file[1]/filename", "hachoir/small_text.tar")
        self.checkValue(parser, "/file[1]/size", 10240)

    def test_7zip(self):
        parser = self.parse("archive.7z")
        self.checkValue(parser, "/signature/major_ver", 0)
        self.checkValue(parser, "/signature/minor_ver", 4)
        self.checkValue(
            parser, "/next_hdr/encoded_hdr/pack_info/pack_pos", 96634)
        self.checkDisplay(
            parser, "/next_hdr/encoded_hdr/pack_info/size_marker", 'kSize')
        self.checkValue(
            parser, "/next_hdr/encoded_hdr/unpack_info/num_folders", 1)

    def test_java_serialized(self):
        parser = self.parse("weka.model")
        self.checkDisplay(
            parser, "/object[0]/classDesc", "weka.classifiers.functions.SMO")
        self.checkDisplay(
            parser, "/object[1]/classDesc", "-> weka.core.Instances")
        self.checkDesc(
            parser, "/object[1]/value/field[2]/value/field[0]",
            "java.util.ArrayList.size")
        self.checkValue(
            parser, "/object[1]/value/field[2]/value/field[0]", 11)

    def test_mpeg_ts(self):
        parser = self.parse("sample.ts")
        self.checkValue(
            parser, "/packet[0]/has_error", False)
        self.checkValue(
            parser, "/packet[0]/has_payload", True)
        self.checkValue(
            parser, "/packet[2]/has_adaptation", True)
        self.checkValue(
            parser, "/packet[2]/adaptation_field/pcr_base", 44)
        self.checkValue(
            parser, "/packet[78]/payload_unit_start", True)

    def test_m2ts(self):
        parser = self.parse("Panasonic_AG_HMC_151.MTS")
        self.checkValue(
            parser, "/packet[0]/has_error", False)
        self.checkValue(
            parser, "/packet[0]/has_payload", True)
        self.checkValue(
            parser, "/packet[3]/has_adaptation", True)
        self.checkValue(
            parser, "/packet[3]/adaptation_field/pcr_base", 153)

    def test_macho_x86_ppc(self):
        parser = self.parse("macos_10.5.macho")
        self.checkDisplay(
            parser, "/file[0]/header/cputype", "PowerPC")
        self.checkDisplay(
            parser, "/file[1]/header/cputype", "i386")
        self.checkValue(
            parser, "/file[0]/load_command[1]/data/segname", "__TEXT")
        self.checkValue(
            parser, "/file[0]/load_command[1]/data/section[1]/sectname", "__symbol_stub1")
        self.checkValue(
            parser, "/file[1]/load_command[1]/data/segname", "__TEXT")
        self.checkValue(
            parser, "/file[1]/load_command[1]/data/section[1]/sectname", "__cstring")

    def test_macho_x86_64(self):
        parser = self.parse("macos_10.12.macho")
        self.checkDisplay(
            parser, "/file[0]/header/cputype", "i386")
        self.checkDisplay(
            parser, "/file[1]/header/cputype", "x86_64")
        self.checkValue(
            parser, "/file[0]/load_command[1]/data/segname", "__TEXT")
        self.checkValue(
            parser, "/file[0]/load_command[1]/data/section[1]/sectname", "__symbol_stub")
        self.checkValue(
            parser, "/file[1]/load_command[1]/data/segname", "__TEXT")
        self.checkValue(
            parser, "/file[1]/load_command[1]/data/section[1]/sectname", "__stubs")

    def test_cr2(self):
        parser = self.parse("canon.raw.cr2")
        self.checkValue(parser, "version", 42)
        self.checkValue(parser, "cr_identifier", "CR")
        self.checkValue(parser, "ifd[0]/entry[0]/tag", 0x0100)
        self.checkValue(parser, "ifd[0]/value[4]", 'Canon')
        self.checkValue(parser, "ifd[0]/value[5]", 'Canon EOS REBEL T5i')

    def test_tga(self):
        parser = self.parse("32bpp.tga")
        self.checkValue(parser, "/width", 800)
        self.checkValue(parser, "/height", 600)
        self.checkValue(parser, "/bpp", 32)
        self.checkDisplay(parser, "/codec", "True-color RLE")


class TestParserRandomStream(unittest.TestCase):

    def test_random_stream(self, tests=(1, 8)):
        a = array('L')
        parser_list = HachoirParserList()
        n = max(tests) * max(parser.getParserTags()
                             ["min_size"] for parser in parser_list)
        k = 8 * a.itemsize
        for i in range((n - 1) // k + 1):
            a.append(random.getrandbits(k))
        a = StringInputStream(a.tobytes(), source="<random data>")
        for parser in parser_list:
            size = parser.getParserTags()["min_size"]
            for test in tests:
                a._size = a._current_size = size * test
                try:
                    parser(a, validate=True)
                    error("[%s] Parser didn't reject random data" %
                          parser.__name__)
                except ValidateError:
                    continue


if __name__ == "__main__":
    setup_tests()
    unittest.main()
