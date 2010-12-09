#!/usr/bin/env python
# -*- coding: utf-8 -*-
DOWNLOAD_SCRIPT = "download_testcase.py"
"""
Test hachoir-parser using the testcase.
Use script %s to download and check the testcase.
""" % DOWNLOAD_SCRIPT

# Configure Hachoir
from hachoir_core import config
config.use_i18n = False  # Don't use i18n
config.quiet = True      # Don't display warnings

from hachoir_core.field import FieldError
from hachoir_core.i18n import getTerminalCharset
from hachoir_core.error import HACHOIR_ERRORS, error
from hachoir_core.stream import InputStreamError, StringInputStream
from hachoir_parser import createParser, HachoirParserList, ValidateError
from hachoir_core.compatibility import all
from locale import setlocale, LC_ALL
from array import array
from datetime import datetime
import random
import os
import sys

###########################################################################

def checkValue(parser, path, value):
    sys.stdout.write("  - Check field %s.value=%s (%s): "
        % (path, repr(value), value.__class__.__name__))
    sys.stdout.flush()
    try:
        read = parser[path].value
        if read == value:
            sys.stdout.write("ok\n")
            return True
        else:
            sys.stdout.write("wrong value (%s, %s)\n"
                % (repr(read), read.__class__.__name__))
            return False
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

def checkDisplay(parser, path, value):
    sys.stdout.write("  - Check field %s.display=%s (%s): "
        % (path, repr(value), value.__class__.__name__))
    sys.stdout.flush()
    try:
        read = parser[path].display
        if read == value:
            sys.stdout.write("ok\n")
            return True
        else:
            sys.stdout.write("wrong value (%s, %s)\n"
                % (repr(read), read.__class__.__name__))
            return False
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

def checkDesc(parser, path, value):
    sys.stdout.write("  - Check field %s.description=%s (%s): "
        % (path, repr(value), value.__class__.__name__))
    sys.stdout.flush()
    try:
        read = parser[path].description
        if read == value:
            sys.stdout.write("ok\n")
            return True
        else:
            sys.stdout.write("wrong value (%s, %s)\n"
                % (repr(read), read.__class__.__name__))
            return False
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

def checkNames(parser, path, names):
    sys.stdout.write("  - Check field names %s=(%s) (%u): "
        % (path, ", ".join(names), len(names)))
    sys.stdout.flush()
    try:
        fieldset = parser[path]
        if len(fieldset) != len(names):
            sys.stdout.write("invalid length (%u)\n" % len(fieldset))
            return False
        names = list(names)
        read = list(field.name for field in fieldset)
        if names != read:
            sys.stdout.write("wrong names (%s)\n" % ", ".join(read))
            return True
        else:
            sys.stdout.write("ok\n")
            return True
    except FieldError, err:
        sys.stdout.write("field error: %s\n" % unicode(err))
        return False

###########################################################################

def checkYellowdude(parser): return (
    checkValue(parser, "/main/version/version", 2),
    checkNames(parser, "/main", ("type", "size", "version", "obj_mat")))

def checkLogoUbuntu(parser): return (
    checkValue(parser, "/header/width", 331),
    checkValue(parser, "/time/second", 46))

def checkClick(parser): return (
    checkValue(parser, "/info/producer/text", "Sound Forge 4.5"),
    checkValue(parser, "/format/sample_per_sec", 22050))

def checkMBR(parser): return (
    checkValue(parser, "/mbr/header[1]/size", 65545200),
    checkDisplay(parser, "/mbr/signature", u"0xaa55"))

def checkFlashMob(parser): return (
    checkValue(parser, "/Segment[0]/Cues/CuePoint[1]/CueTrackPositions[0]"
          + "/CueClusterPosition/cluster/BlockGroup[14]/Block/block/timecode", 422),
    checkValue(parser, "/Segment[0]/Tags[0]/Tag[0]/SimpleTag[3]/TagString/unicode",
          u"\xa9 dadaprod, licence Creative Commons by-nc-sa 2.0 fr"))

def check10min(parser): return (
    checkValue(parser, "/Segment[0]/size", None),
    checkValue(parser, "/Segment[0]/Tracks[0]/TrackEntry[0]/CodecID/string", "V_MPEG4/ISO/AVC"))

def checkWormuxICO(parser): return (
    checkValue(parser, "icon_header[0]/height", 16),
    checkValue(parser, "icon_data[0]/header/hdr_size", 40))

def checkCDA(parser): return (
    checkValue(parser, "filesize", 36),
    checkValue(parser, "/cdda/track_no", 4),
    checkDisplay(parser, "/cdda/disc_serial", "0008-5C48"),
    checkValue(parser, "/cdda/rb_length/second", 53))

def checkSheepMP3(parser): return (
    checkValue(parser, "/id3v2/field[6]/content/text",
        u'Stainless Steel Provider is compilated to the car of Twinstar.'),
    checkValue(parser, "/frames/frame[0]/use_padding", False))

def checkAU(parser): return (
    checkValue(parser, "info", "../tmp/temp.snd"),
    checkDisplay(parser, "codec", "8-bit ISDN u-law"))

def checkGzip(parser):
    return (checkValue(parser, "filename", "test.txt"),)

def checkSteganography(parser): return (
    checkValue(parser, "/frames/padding[0]", "misc est un canard\r"),
    checkDesc(parser, "/frames", 'Frames: Variable bit rate (VBR)'),
    checkDesc(parser, "/frames/frame[1]", u'MPEG-1 layer III, 160.0 Kbit/sec, 44.1 kHz'))

def checkRPM(parser): return (
    checkValue(parser, "name", "ftp-0.17-537"),
    checkValue(parser, "os", 1),
    checkValue(parser, "checksum/content_item[2]/value", 50823),
    checkValue(parser, "header/content_item[15]/value", "ftp://ftp.uk.linux.org/pub/linux/Networking/netkit"))

def checkJPEG(parser): return (
    checkValue(parser, "app0/content/jfif", "JFIF\x00"),
    checkValue(parser, "app0/content/ver_maj", 1),
    checkValue(parser, "photoshop/content/signature", "Photoshop 3.0"),
    checkValue(parser, "photoshop/content/copyright_flag/content", 0),
    checkValue(parser, "exif/content/header", "Exif\0\0"),
    checkValue(parser, "exif/content/version", 42))

def checkTAR(parser): return (
    checkDisplay(parser, "file[0]/name", u'"dummy.txt"'),
    checkDisplay(parser, "file[1]/mode", u'"0000755"'),
    checkDisplay(parser, "file[1]/type", u'Directory'),
    checkDisplay(parser, "file[2]/devmajor", u'(empty)'),
)

def checkRAR(parser): return (
    checkValue(parser, "archive_start/crc16", 0x77E1),
    checkValue(parser, "new_sub_block[0]/crc16", 0x2994),
    checkValue(parser, "file[0]/crc32", 0x4C6D13ED),
    checkValue(parser, "new_sub_block[1]/crc32", 0x34528E23),
    checkValue(parser, "file[1]/filename", ".svn\prop-base\README.svn-base"),
    checkValue(parser, "new_sub_block[1]/filename", u'ACL'),
    #archive_end bad candidate for checking
    checkValue(parser, "new_sub_block[362]/crc32", 0x6C84C95E),
)

def checkACE(parser): return (
    checkValue(parser, "header/crc16", 0xA9BE),
    checkValue(parser, "file[0]/reserved", 0x4554),
    checkValue(parser, "file[1]/filename", "hachoir_core\.svn"),
    checkValue(parser, "file[2]/parameters", 0x000A),
    #End of archive, lots of work...
    #checkValue(parser, "new_recovery[0]/signature", "**ACE**"),
)

def checkCornerBMP(parser): return (
    checkValue(parser, "header/width", 189),
    checkValue(parser, "header/used_colors", 70),
    checkDesc(parser, "palette/color[1]", "RGB color: White (opacity: 0%)"),
    checkValue(parser, "pixels/line[26]/pixel[14]", 28),
)

def checkCACertClass3(parser): return (
    checkDisplay(parser, "seq[0]/class", u'universal'),
    checkDesc(parser, "seq[0]/seq[0]/seq[1]/obj_id[0]", "Object identifier: 1.2.840.113549.1.1.4"),
    checkValue(parser, "seq[0]/seq[0]/seq[2]/set[0]/seq[0]/print_str[0]/value", u"Root CA"),
    checkValue(parser, "seq[0]/seq[0]/seq[2]/set[3]/seq[0]/ia5_str[0]/value", u"support@cacert.org"),
    checkValue(parser, "seq[0]/bit_str[0]/size", 513),
)

def checkPYC(parser): return (
    checkValue(parser, "/content/consts/item[0]", 42),
    checkValue(parser, "/content/stack_size", 4),
    checkValue(parser, "/content/consts/item[1]", 2535301200456458802993406410752L),
    checkValue(parser, "/content/consts/item[4]", 0.3j),
    checkValue(parser, "/content/consts/item[8]", "abc"),
    checkValue(parser, "/content/filename", "pyc_example.py"))

def checkReferenceMapClass(parser): return (
    checkValue(parser, "/minor_version", 3),
    checkValue(parser, "/major_version", 45),
    checkValue(parser, "/constant_pool_count", 326),
    checkValue(parser, "/constant_pool/constant_pool[324]/bytes", u"([Ljava/lang/Object;Ljava/lang/Object;)V"),
    checkValue(parser, "/super_class", 80),
    checkValue(parser, "/interfaces_count", 0),
    checkValue(parser, "/fields_count", 16),
    checkValue(parser, "/fields/fields[3]/attributes/attributes[0]/attribute_name_index", 93),
    checkValue(parser, "/methods_count", 31),
    checkValue(parser, "/methods/methods[30]/attributes/attributes[0]/code_length", 5),
    checkValue(parser, "/attributes_count", 3),
    checkValue(parser, "/attributes/attributes[2]/classes/classes[1]/inner_name_index", 83))

def checkClaqueBeignet(parser): return (
    checkDesc(parser, "rect", "Rectangle: 550x400"),
    checkDisplay(parser, "frame_rate", "24.0"),
    checkDesc(parser, "bkgd_color[0]/color", "RGB color: #CC9933"),
    checkDisplay(parser, "def_sound[0]/rate", "11.0 kHz"),
    checkValue(parser, "def_sound[0]/len", 1661),
    checkValue(parser, "sound_hdr2[0]/sound_is_16bit", False),
    checkValue(parser, "export[0]/export[0]/name", u"C bras"),
)

def checkBreakdance(parser): return (
    checkDisplay(parser, "/audio[0]/codec", "MP3"),
    checkValue(parser, "/audio[2]/timestamp", 52),
    checkDisplay(parser, "/video[0]/codec", "Sorensen H.263"),
    checkValue(parser, "/metadata/entry[1]/item[8]/attr[1]/item[4]/value/exponent", 20),
)

def checkArpDnsPingDns(parser): return (
    checkValue(parser, "/packet[5]/ipv4/ttl", 120),
    checkDisplay(parser, "/packet[3]/ts_epoch", "2006-11-23 23:13:19"),
    checkValue(parser, "/packet[3]/ipv4/src", "212.27.54.252"),
    checkDisplay(parser, "/packet[7]/udp/src", "DNS"),
)

def checkExt2(parser): return (
    checkDisplay(parser, "/superblock/last_check", u'2006-12-04 22:56:37'),
    checkDisplay(parser, "/superblock/creator_os", "Linux"),
    checkValue(parser, "/group_desc/group[0]/block_bitmap", 3),
    checkValue(parser, "/group_desc/group[0]/free_blocks_count", 44),
    checkValue(parser, "/group[0]/block_bitmap/item[9]", False),
    checkDisplay(parser, "/group[0]/inode_table/inode[1]/file_type", "Directory"),
    checkDesc(parser, "/group[0]/inode_table/inode[10]", u"Inode 11: file, size=1024 bytes, mode=drwxr-xr-x"),
    checkValue(parser, "/group[0]/inode_table/inode[11]/size", 1816),
    checkDisplay(parser, "/group[0]/inode_table/inode[11]/ctime", u'2006-12-04 23:22:00'),
)

def checkArticle01(parser): return (
    checkDisplay(parser, "/header/red_mask", u'0x00ff0000'),
    checkDisplay(parser, "/header/color_space", "Business (Saturation)"),
    checkValue(parser, "/pixels/line[94]/pixel[11]", 15265520),
)

def checkReiserFS3(parser): return (
    checkValue(parser, "/superblock/root_block", 645),
    checkDisplay(parser, "/superblock/hash_function", "R5_HASH"),
    checkValue(parser, "/superblock/tree_height", 3),
)

def checkLaraCroft(parser): return (
    checkDesc(parser, "/palette_4bits/color[8]", "RGB color: #100000"),
    checkDesc(parser, "/palette_8bits/color[0]", "RGB color: Black"),
    checkValue(parser, "/compression", 1),
    checkValue(parser, "/horiz_dpi", 500),
)

def checkLinuxSwap(parser): return (
    checkValue(parser, "/version", 1),
    checkValue(parser, "/last_page", 9),
    checkValue(parser, "/magic", u"SWAPSPACE2"),
)

def checkPikachu(parser): return (
    checkValue(parser, "/max_record_size", 510),
    checkValue(parser, "/func[2]/y", 10094),
    checkDisplay(parser, "/func[4]/brush_style", u"Solid"),
    checkValue(parser, "/func[10]/object_id", 2),
)

def checkGlobe(parser): return (
    checkValue(parser, "/file_size", 3923),
    checkValue(parser, "/func[1]/x", 9989),
    checkDisplay(parser, "/func[4]/operation", u"Copy pen (P)"),
    checkDisplay(parser, "/func[9]/brush_style", u"Null"),
)

def checkIndiana(parser): return (
    checkDesc(parser, "/header", u"Multiple tracks, synchronous; 3 tracks"),
    checkDisplay(parser, "/track[0]/command[1]/microsec_quarter", u"300.00 ms"),
    checkDisplay(parser, "/track[1]/command[6]/note", u"A (octave 5)"),
    checkValue(parser, "/track[1]/command[8]/time", 408),
    checkValue(parser, "/track[1]/command[8]/velocity", 80),
)

def checkGrassLogo(parser): return (
    checkValue(parser, "/func[4]/y", 297),
    checkDesc(parser, "/func[15]", u"Begin path"),
    checkDesc(parser, "/func[40]/color", u"RGB color: #008F00 (opacity: 0%)"),
    checkValue(parser, "/emf_header/maj_ver", 1),
    checkValue(parser, "/emf_header/width_px", 1024),
    checkValue(parser, "/emf_header/width_mm", 270),
    checkValue(parser, "/emf_header/description", "Adobe Illustrator EMF 8.0"),
)

def checkIndiaMap(parser): return (
    checkValue(parser, "/screen/global_map", True),
    checkDesc(parser, "/color_map/color[0]", u"RGB color: Black"),
    checkValue(parser, "/image[0]/height", 794),
)

def checkCercle(parser): return (
    checkValue(parser, "/msdos/reloc_offset", 28),
    checkDisplay(parser, "/msdos/init_cs_ip", "0x00000315"),
)

def checkEula(parser): return (
    checkDisplay(parser, "/pe_header/cpu", "Intel 80386"),
    checkDisplay(parser, "/pe_opt_header/subsystem", "Windows GUI"),
    checkDisplay(parser, "/pe_opt_header/import/rva", "0x00008314"),
    checkDisplay(parser, "/section_hdr[1]/mem_size", "4632 bytes"),
    checkValue(parser, "/section_hdr[1]/is_readable", True),
    checkValue(parser, "/section_hdr[1]/is_executable", False),
    checkValue(parser, "/section_rsrc/version_info/node[0]/node[1]/node[0]/node[0]/value", u"Dell Inc"),
    checkDesc(parser, "/section_rsrc/icon[0]/bmp_header", "Bitmap info header: 16x32 pixels, 4 bits/pixel"),
    checkDesc(parser, "/section_rsrc/icon[1]", "Resource #296 content: type=3"),
)

def checkOCR10(parser): return (
    checkValue(parser, "/chars/char[3]/data_offset", 201),
    checkValue(parser, "/chars/char[8]/width_pixels", 10),
)

def checkKino14(parser): return (
    checkValue(parser, "/max_char_width", 26),
    checkValue(parser, "/char_codes/char[5]", 5),
    checkValue(parser, "/chars/char[1]/data_offset", 1),
    checkValue(parser, "/chars/char[1]/height_pixels", 13),
    checkValue(parser, "/char_data/char_bitmap[3]/line[1]/pixel[0]", 128),
)

def checkFreeSoftwareSong(parser): return (
    checkDisplay(parser, "/blocksize", u"'9'"),
    checkDisplay(parser, "/file/crc32", u"0x8c3c1b7b"),
)

def checkPing(parser): return (
    checkDisplay(parser, "/header/class", u"32 bits"),
    checkDisplay(parser, "/header/endian", u"Little endian"),
    checkDisplay(parser, "/header/type", u"Executable file"),
    checkDisplay(parser, "/header/machine", u"Intel 80386"),
    checkValue(parser, "/header/phentsize", 32),
    checkDisplay(parser, "/prg_header[1]/type", u"Program interpreter"),
)

def checkGeorgia(parser): return (
    checkDisplay(parser, "/minor_version", "3"),
    checkDisplay(parser, "/major_version", "1"),
    checkDesc(parser, "/file[0]", u'File "fontinst.inf" (64 bytes)'),
    checkValue(parser, "/file[1]/filename", u"Georgiaz.TTF"),
)

def checkDebianTorrent(parser): return (
    checkValue(parser, "/root/announce", u"http://bttracker.acc.umu.se:6969/announce"),
    checkValue(parser, "/root/comment", u'"Debian CD from cdimage.debian.org"'),
    checkDisplay(parser, "/root/creation_date", u'2006-11-16 21:44:37'),
    checkDisplay(parser, "/root/info/value/length", u"638.7 MB"),
    checkDisplay(parser, "/root/info/value/piece_length", u"512.0 KB"),
)

def checkDell8FAT16(parser): return (
    checkValue(parser, "/boot/oem_name", u"Dell 8.0"),
    checkDisplay(parser, "/boot/serial", u"0x07d6090d"),
    checkValue(parser, "/boot/label", u"DellUtility"),
    checkValue(parser, "/boot/fs_type", u"FAT16"),
    checkValue(parser, "/fat[1]/group[0]/entry[2]", 3),
    checkDisplay(parser, "/fat[0]/group[4]/entry[8]", u"free cluster"),
    checkDesc(parser, "/root[0]/entry[0]", u"Long filename part: 'command.com' [65]"),
    checkDesc(parser, "/root[0]/entry[1]", u"File: 'COMMAND.COM'"),
    checkValue(parser, "/root[0]/entry[2]/hidden", True),
    checkDesc(parser, "/root[0]/entry[2]/create", u"2006-09-13 15:01:16"),
    checkDesc(parser, "/root[0]/entry[2]/access", u"2006-09-13"),
    checkDesc(parser, "/root[0]/entry[2]/modify", u"2005-07-26 00:48:26"),
    checkValue(parser, "/root[0]/entry[2]/size", 29690),
)

def checkXM(parser): return (
    checkValue(parser, "/header/title", u"Dont you... voguemix"),
    checkValue(parser, "/header/bpm", 128),
    checkValue(parser, "/pattern[0]/data_size", 708),
    checkDisplay(parser, "/pattern[0]/row[0]/note[0]/note", "F (octave 5)"),
    checkValue(parser, "/pattern[0]/row[0]/note[0]/effect_parameter", 0x0A),
    checkDisplay(parser, "/pattern[0]/row[0]/note[1]/note", "A (octave 5)"),
    checkValue(parser, "/pattern[0]/row[0]/note[1]/effect_parameter", 0x80),
    checkValue(parser, "/pattern[20]/data_size", 1129),
    checkDisplay(parser, "/pattern[20]/row[0]/note[0]/note", "C# (octave 5)"),
    checkValue(parser, "/pattern[20]/row[0]/note[0]/instrument", 5),
    checkValue(parser, "/instrument[3]/name", u"Vogue of Triton"),
    checkValue(parser, "/instrument[4]/second_header/panning_points", 6),
    checkValue(parser, "/instrument[20]/name", u"808-hi5.smp"),
)

def checkS3M(parser): return (
    checkValue(parser, "/header/title", "Satellite one."),
    checkValue(parser, "/instrument[0]/sample_offset", 27024),
    checkValue(parser, "/instrument[0]/c4_speed", 8363),
    checkValue(parser, "/instrument[0]/name", "By Purple Motion of"),
    checkValue(parser, "/instrument[1]/name", "Future Crew - 1993"),
    checkValue(parser, "/pattern[0]/row[0]/note[0]/volume", 54),
)

def checkPTM(parser): return (
    checkValue(parser, "/header/title", "Anti-arpeggio tune!-VV/AcMe"),
    checkValue(parser, "/instrument[0]/sample_offset", 30928),
    checkValue(parser, "/instrument[0]/c4_speed", 8363),
    checkValue(parser, "/instrument[0]/name", "Yep guess wat...."),
    checkValue(parser, "/instrument[1]/name", "Mag ik even mijn ongenoegen"),
    checkValue(parser, "/instrument[1]/gus_loop_flags", 0),
    checkValue(parser, "/pattern[0]/row[0]/note[0]/effect", 15),
)

def checkVimLNK(parser): return (
    checkValue(parser, "/creation_time", datetime(2006, 5, 7, 14, 18, 32)),
    checkValue(parser, "/target_filesize", 1363968),
)

def checkSevenzipCHM(parser): return (
    checkValue(parser, "/itsf/version", 3),
    checkDisplay(parser, "/itsf/lang_id", u"Russian"),
    checkValue(parser, "/itsf/dir_uuid/time", datetime(1997, 1, 31, 20, 42, 14, 890625)),
    checkDisplay(parser, "/itsf/stream_uuid/variant", u"Microsoft Corporation"),
    checkDisplay(parser, "/itsf/stream_uuid/mac", u'INTEL CORPORATION - HF1-06 [22:e6:ec]'),
    checkDisplay(parser, "/file_size/file_size", u"75.6 KB"),
    checkDisplay(parser, "/dir/itsp/lang_id", u"English United States"),
    checkValue(parser, "/dir/pmgl[0]/entry[1]/name", u"/#IDXHDR"),
)

def checkSwat(parser): return (
    checkValue(parser, "flags", 8),
    checkValue(parser, "height", 256),
    checkValue(parser, "width", 256),
    checkValue(parser, "jpeg_header_len", 10),
)

def checkFile(filename, check_parser):
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
    return all(check_parser(parser))

def testFiles(directory):
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
        except OSError:
             print "Unable to create directory: %s" % directory
             return False

    for filename, check_parser in testcase_files:
        fullname = os.path.join(directory, filename)
        try:
            os.stat(fullname)
        except OSError:
            print >>sys.stderr, \
                "[!] Error: file %s is missing, " \
                "use script %s to fix your testcase" % \
                (filename, DOWNLOAD_SCRIPT)
            return False

        print "[+] Test %s:" % filename
        if not checkFile(fullname, check_parser):
            return False
    return True


def testRandom(seed=0, tests=(1,8)):
    random.seed(seed)
    a = array('L')
    parser_list = HachoirParserList()
    n = max(tests) * max(parser.getParserTags()["min_size"] for parser in parser_list)
    k = 8 * a.itemsize
    for i in xrange((n - 1) // k + 1):
        a.append(random.getrandbits(k))
    a = StringInputStream(a.tostring(), source="<random data>")
    ok = True
    for parser in parser_list:
        size = parser.getParserTags()["min_size"]
        for test in tests:
            a._size = a._current_size = size * test
            try:
                parser(a, validate=True)
                error("[%s] Parser didn't reject random data" % parser.__name__)
            except ValidateError:
                continue
            except HACHOIR_ERRORS, err:
                error(u"[%s] %s" % (parser.__name__, err))
            ok = False
    return ok


def main():
    setlocale(LC_ALL, "C")
    if len(sys.argv) != 2:
        print >>sys.stderr, "usage: %s testcase_directory" % sys.argv[0]
        sys.exit(1)
    charset = getTerminalCharset()
    directory = unicode(sys.argv[1], charset)

    print "Test hachoir-parser using random data."
    print
    if not testRandom():
        print
        print "If you are really sure there is no error in your code," \
              " increment the 'seed' parameter of testRandom."
        sys.exit(1)
    print "Result: ok"

    print
    print "Test hachoir-parser using testcase."
    print
    print "Testcase is in directory: %s" % directory
    if not testFiles(directory):
        print
        for index in xrange(3):
            print "!!! ERROR !!!"
        print
        sys.exit(1)
    print
    print "Result: ok for the %s files" % len(testcase_files)

testcase_files = (
    (u"yellowdude.3ds", checkYellowdude),
    (u"logo-kubuntu.png", checkLogoUbuntu),
    (u"mbr_linux_and_ext", checkMBR),
    (u"kde_click.wav", checkClick),
    (u"test.txt.gz", checkGzip),
    (u"flashmob.mkv", checkFlashMob),
    (u"10min.mkv", check10min),
    (u"cd_0008_5C48_1m53s.cda", checkCDA),
    (u"wormux_32x32_16c.ico", checkWormuxICO),
    (u"audio_8khz_8bit_ulaw_4s39.au", checkAU),
    (u"sheep_on_drugs.mp3", checkSheepMP3),
    (u"pyc_example_1.5.2.pyc", checkPYC),
    (u"pyc_example_2.2.3.pyc", checkPYC),
    (u"pyc_example_2.5c1.pyc", checkPYC),
    (u"ftp-0.17-537.i586.rpm", checkRPM),
    # cross.xcf
    (u"jpeg.exif.photoshop.jpg", checkJPEG),
    (u"small_text.tar", checkTAR),
    (u"cacert_class3.der", checkCACertClass3),
    (u"kde_haypo_corner.bmp", checkCornerBMP),
    # png_331x90x8_truncated.png
    (u"steganography.mp3", checkSteganography),
    # smallville.s03e02.avi
    # 08lechat_hq_fr.mp3
    (u"ReferenceMap.class", checkReferenceMapClass),
    (u"claque-beignet.swf", checkClaqueBeignet),
    # interlude_david_aubrun.ogg
    (u"breakdance.flv", checkBreakdance),
    (u"arp_dns_ping_dns.tcpdump", checkArpDnsPingDns),
    # matrix_ping_pong.wmv
    # usa_railroad.jpg
    (u"my60k.ext2", checkExt2),
    (u"article01.bmp", checkArticle01),
    (u"reiserfs_v3_332k.bin", checkReiserFS3),
    (u"lara_croft.pcx", checkLaraCroft),
    # hero.tga
    # firstrun.rm
    (u"linux_swap_9pages", checkLinuxSwap),
    (u"pikachu.wmf", checkPikachu),
    (u"globe.wmf", checkGlobe),
    (u"indiana.mid", checkIndiana),
    # 25min.aifc
    (u"grasslogo_vector.emf", checkGrassLogo),
    (u"ocr10.laf", checkOCR10),
    (u"kino14s.laf", checkKino14),
    # ladouce_1h15.wav
    (u"hachoir-core.ace", checkACE),
    (u"hachoir-core.rar", checkRAR),
    (u"debian-31r4-i386-binary-1.iso.torrent", checkDebianTorrent),
    (u"india_map.gif", checkIndiaMap),
    (u"cercle.exe", checkCercle),
    (u"eula.exe", checkEula),
    (u"free-software-song.midi.bz2", checkFreeSoftwareSong),
    (u"ping_20020927-3ubuntu2", checkPing),
    (u"georgia.cab", checkGeorgia),
    # hachoir.org.sxw
    (u"dell8.fat16", checkDell8FAT16),
    (u"dontyou.xm", checkXM),
    (u"satellite_one.s3m", checkS3M),
    (u"anti-arpeggio_tune.ptm", checkPTM),
    # deja_vu_serif-2.7.ttf
    # twunk_16.exe
    (u"vim.lnk", checkVimLNK),
    (u"7zip.chm", checkSevenzipCHM),
    # green_fire.jpg
    # marc_kravetz.mp3
    # pentax_320x240.mov
    # gps.jpg
    # angle-bear-48x48.ani
    # hotel_california.flac
    # radpoor.doc
    # quicktime.mp4
    (u"swat.blp", checkSwat),
)

if __name__ == "__main__":
    main()

