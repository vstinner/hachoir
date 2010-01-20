#!/usr/bin/env python2.4
"""
Download and check Hachoir testcase. Files are downloaded from:
  http://hachoir.tuxfamily.org/testcase/
"""
TESTCASE_URL = "http://hachoir.tuxfamily.org/testcase/"

from urllib2 import Request, urlopen, URLError, HTTPError
from hachoir_core.i18n import getTerminalCharset
from hachoir_core.tools import humanFilesize
try:
    from md5 import md5
except ImportError:
    md5 = None
import os
import sys
import stat

testcase_files = (
    (u"yellowdude.3ds", 48116, "2e1301e23518fbed06dd0a739e110c9e"),
    (u"logo-kubuntu.png", 10022, "336368f689952e18e9197aaa1caf8ebb"),
    (u"mbr_linux_and_ext", 512, "18730e496f263cb639b0a07152e49444"),
    (u"kde_click.wav", 1824, "02bee988149cc7c21f4b56176f2c7a2f"),
    (u"test.txt.gz", 117, "037e1908f6e081d8178811107c196239"),
    (u"flashmob.mkv", 1326518, "52ad0e32fc368d80107727f8d470579f"),
    (u"10min.mkv", 120697, "0bd4adc27cc95effc960ab85b5737d48"),
    (u"cd_0008_5C48_1m53s.cda", 44, "f219b3083b2ebacbd9728fd198e2a459"),
    (u"wormux_32x32_16c.ico", 1150, "278e578b6b9c404f921107876a7fbf9e"),
    (u"audio_8khz_8bit_ulaw_4s39.au", 35224, "87458dca42f2e027ca86e592172eea74"),
    (u"sheep_on_drugs.mp3", 21038, "7740bf3a7908bddcfff2c2ba2347d3d9"),
    (u"pyc_example_1.5.2.pyc", 380, "47bffae903a89a48ac3b01625c4e1eec"),
    (u"pyc_example_2.2.3.pyc", 649, "4fd08601b28dce8b0bab56e67920ef94"),
    (u"pyc_example_2.5c1.pyc", 584, "372fa5e9e50230fc382997638813ae2f"),
    (u"ftp-0.17-537.i586.rpm", 51183, "98a598d6e47ea0fbb999d5163558d3a0"),
    (u"cross.xcf", 1816, "f4e834f4fbf9a479aae46d457b14b786"),
    (u"jpeg.exif.photoshop.jpg", 10057, "12e4c375706f19da2bed5bac321564bf"),
    (u"small_text.tar", 10240, "91128f90b3c7f48579b2123804860167"),
    (u"cacert_class3.der", 1548, "733f35541d44c9e95a4aef51ad0306b6"),
    (u"kde_haypo_corner.bmp", 8590, "ee7713cf238977d9751e5cc043878659"),
    (u"png_331x90x8_truncated.png", 100, "ca63f46b0f5d1e8cd19717f3f51004d6"),
    (u"steganography.mp3", 1168, "b91c9cf93306b47f698f60f6636eb40b"),
    (u"smallville.s03e02.avi", 10748, "7bb544a5f1d71f16ab9b7e12032ca895"),
    (u"08lechat_hq_fr.mp3", 3010, "002c051c616593620b1cb419ec7ba5ca"),
    (u"ReferenceMap.class", 9118, "66bfa8670ca13d2189f8c706080ab079"),
    (u"claque-beignet.swf", 288769, "aede88619acb56b1ba43d8350450feab"),
    (u"interlude_david_aubrun.ogg", 936599, "3524cd6d25842566bc3993ba568c213c"),
    (u"breakdance.flv", 1686478, "01b66af40e8d0d743978ca7615392af9"),
    (u"arp_dns_ping_dns.tcpdump", 797, "3260300bb993d5034f7d5e80eed80240"),
    (u"matrix_ping_pong.wmv", 3581941, "13ee1776070a9804771198dd491923ad"),
    (u"usa_railroad.jpg", 103748, "5c19d197968e6135da1f172cab23ad46"),
    (u"my60k.ext2", 61440, "3f456ab30e0798b315124b76f7f89027"),
    (u"article01.bmp", 29722, "1339736f6e7eab841d07e6e341d156b2"),
    (u"reiserfs_v3_332k.bin", 333312, "b8537b3fdd79b1aa113d9cb41ed775ab"),
    (u"lara_croft.pcx", 41072, "1046053da6e208ea41c7fa3647b4fa97"),
    (u"hero.tga", 64786, "7bc9d3d77c4c614d2586760295b4c078"),
    (u"firstrun.rm", 75534, "5aa56f5de2723294136fadb90fc5b2ce"),
    (u"linux_swap_9pages", 40960, "f6a860270f85978b00706fd55203f3a3"),
    (u"pikachu.wmf", 16792, "ac542e397b6417245385cab6fd0036a4"),
    (u"globe.wmf", 7846, "9b24434cd114ceaf4c6fd031886b9325"),
    (u"indiana.mid", 30610, "75ef10d31eab5a88d190c754d5c77dd8"),
    (u"25min.aifc", 100, "b946ea4ea8b50d41bd9e975cf0335f18"),
    (u"grasslogo_vector.emf", 6932, "6fe03cdf34ac3ee6e797c7aeb8c92e41"),
    (u"ocr10.laf", 17264, "4f0a15d2abe84c5e4bd1eca11195dc87"),
    (u"kino14s.laf", 30957, "9fbb52a92ff9db88b85a57cf4359acd8"),
    (u"ladouce_1h15.wav", 5112, "964250e59d1967ab86d60e635a298bbe"),
    (u"hachoir-core.ace", 156483, "00ecf6575dbc2fc4fb90afd4146d0cb3"),
    (u"hachoir-core.rar", 184109, "049e3c0702a7ae42cf4469280a32be93"),
    (u"debian-31r4-i386-binary-1.iso.torrent", 25793, "b68ed9799168d10854e9d10e45d51516"),
    (u"india_map.gif", 35019, "026f17c987c0e61d486963157a230114"),
    (u"cercle.exe", 17056, "cc4227ac437e4a7f04ccd61d3738cbb9"),
    (u"eula.exe", 45056, "5d758e2df701ce642fef3c8d8b4f51f6"),
    (u"free-software-song.midi.bz2", 463, "1ab6ceaf0cd7d8ada4b85ad65d7ffcf0"),
    (u"ping_20020927-3ubuntu2", 30804, "7c856de09bbed6c51eb6dfb20f311f9b"),
    (u"georgia.cab", 311069, "28a1530d591b35c5c9485b4cb6f778da"),
    (u"hachoir.org.sxw", 14781, "26ce99711c8c17a3c6bba299a3cfa68b"),
    (u"dell8.fat16", 113152, "bcef23dc13307ebd464562c6afbf01d3"),
    (u"dontyou.xm", 150672, "2b6077fae78930e804bf3541f8700cf2"),
    (u"satellite_one.s3m", 39778, "4993611aca1474535d6396e01f86cca8"),
    (u"anti-arpeggio_tune.ptm", 175557, "34e39f476f48abe5e41d6e9a88af515e"),
    (u"deja_vu_serif-2.7.ttf", 205708, "a1d6d07d9be2ced64cf9b7e3ddadd399"),
    (u"twunk_16.exe", 49680, "f36a271706edd23c94956afb56981184"),
    (u"vim.lnk", 1510, "9853258788fc67ce406201773d1f4fb5"),
    (u"7zip.chm", 77414, "2ac9ef6c4f4a770b27bc3471c1ee1d31"),
    (u'green_fire.jpg', 2455, '13775aa085ed3fd6da07cf5c6dd8cfe9'),
    (u"marc_kravetz.mp3", 62208, "b1b133498d3e5a807a361ae8931adbc8"),
    (u"pentax_320x240.mov", 1938, "e23aae570cf3a30294e7630ece397d33"),
    (u"gps.jpg", 8271, "15262738e24b85ad4f6199df348e867e"),
    (u"angle-bear-48x48.ani", 29658, "9aa43520cf430bd996c4c318b905bc7f"),
    (u"hotel_california.flac", 32768, "ebd87fc310d8958c9d86ef65c7a20e1d"),
    (u"radpoor.doc", 103936, "114835a03be92e02029c74ece1162c3e"),
    (u"quicktime.mp4", 245779, "dc77a8de8c091c19d86df74280f6feb7"),
    (u"swat.blp", 55753, "a47a2d6ef61c9005c3f5faf1bca253af"),
)

def stringMD5(text):
    if md5:
        return md5(text).hexdigest()
    else:
        return None

def checkFileMD5(filename, correct):
    if not md5:
        print "  - Skip MD5 sum test (no md5 module)"
        return True
    sys.stdout.write("  - Check MD5 sum (%s): " % correct)
    sys.stdout.flush()
    checksum = md5()
    stream = open(filename, "rb")
    while True:
        data = stream.read(4096)
        if not data:
            break
        checksum.update(data)
    hexsum = checksum.hexdigest()
    if hexsum != correct:
        sys.stdout.write("invalid (%s)!\n" % hexsum)
        return False
    else:
        sys.stdout.write("ok\n")
        return True

def download(url, filesize, md5sum, destname):
    sys.stdout.write("[+] Download file %s (%s): " \
        % (url, humanFilesize(filesize)))
    sys.stdout.flush()

    # Download data
    request = Request(url)
    try:
        stream = urlopen(request)
    except HTTPError, err:
        if err.code == 404:
            print "File not found (HTTP error 404)!"
        else:
            print "HTTP error (%s)" % unicode(err)
        return False
    except URLError, err:
        print "URL error (%s)" % unicode(err)
        return False
    data = stream.read()

    # Check downloaded data size
    if len(data) != filesize:
        sys.stdout.write("invalid size (%s)!\n" % len(data))
        return False

    # Check MD5 sum
    computed = stringMD5(data)
    if computed and computed != md5sum:
        sys.stdout.write("invalid MD5 (%s)!\n" % hash)
        return False

    # Write file
    try:
        open(destname, "wb").write(data)
    except IOError, err:
        charset = getTerminalCharset()
        errmsg = unicode(str(err), charset)
        sys.stdout.write("I/O error (%s)\n" % errmsg)
        try:
            os.unlink(destname)
        except OSError:
            pass
        return False
    sys.stdout.write("ok\n")
    return True

def testFiles(directory, url_prefix):
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
        except OSError:
             print "Unable to create directory: %s" % directory
             return False

    for item in testcase_files:
        # Download file if it doesn't exist
        filename, filesize, md5sum = item
        fullname = os.path.join(directory, filename)
        try:
            # Check file MD5
            read = os.stat(fullname)[stat.ST_SIZE]
            print "[+] Test %s: " % filename
            if read != filesize:
                print "  - Invalid file size (%s instead of %s)!" \
                    % (read, filesize)
                return False
            if not checkFileMD5(fullname, md5sum):
                return False
        except OSError:
            # Error: file doesn't exist
            if not download(url_prefix+filename, filesize, md5sum, fullname):
                return False
    return True

def main():
    if len(sys.argv) != 2:
        print >>sys.stderr, "usage: %s directory" % sys.argv[0]
        sys.exit(1)
    charset = getTerminalCharset()
    directory = unicode(sys.argv[1], charset)

    print "Download and check Hachoir testcase."
    print
    print "Use directory: %s" % directory
    ok = testFiles(directory, TESTCASE_URL)
    if not stringMD5("abc"):
        print
        for index in xrange(3):
            print "!!! Warning: Python module md5 is missing, unable to check MD5 hash"
    if ok:
        print
        totalsize = sum( item[1] for item in testcase_files )
        print "Test case is ok (%s files, %s)" % (len(testcase_files), humanFilesize(totalsize))
        sys.exit(0)
    else:
        print
        for index in xrange(3):
            print "!!! ERROR !!!"
        print
        sys.exit(1)

if __name__ == "__main__":
    main()

