#!/usr/bin/env python

from os import path, getcwd, access, R_OK, unlink, nice, mkdir, system, popen4, rename
from os.path import basename
from sys import exit, argv, stderr
from glob import glob
import sha
import random
from random import randint
from array import array
from cStringIO import StringIO

from hachoir_core.cmd_line import unicodeFilename
from hachoir_core.log import log as hachoir_logger, Log
from hachoir_core.stream import InputIOStream, InputStreamError
from hachoir_metadata import extractMetadata
from hachoir_parser import guessParser

def mangle(data):
    hsize = len(data)-1
    max_count = hsize // 100
    max_count = max(max_count, 4)
    count = randint(1, max_count)
    for index in xrange(count):
        off = randint(0, hsize)
        c = randint(0, 255)
        if randint(0, 1) == 1:
            c |= 128
        data[off] = c

class Fuzzer:
    def __init__(self):
        self.filedb = []
        self.tmp_file = "/tmp/stress-hachoir"
        self.nb_error = 0

    def load(self, TEST_FILES):
        self.filedb = glob(path.join(TEST_FILES, "*.*"))
        if not self.filedb:
            print "Empty directory: %s" % TEST_FILES
            exit(1)

    def newLog(self, level, prefix, text, context):
        if level < Log.LOG_ERROR:
            return
        if "Error: Can't get field \"" in text:
            return
        if "Unable to create value" in text:
            return
        self.log_error += 1
        print "METADATA ERROR: %s %s" % (prefix, text)

    def fuzz(self):
        self.nb_error=0
        unlink_tmp_file = False
        hachoir_logger.use_print = False
        hachoir_logger.on_new_message = self.newLog

        while True:
            try:
                test_file = random.choice(self.filedb)
                print "total: %s error -- test file: %s" % (self.nb_error, basename(test_file))

                # Load bytes
                data = open(test_file, "rb").read(MAX_SIZE)
                data = array('B', data)

                # Mangle
                size = len(data)
                mangle(data)

                # Run metadata
                data = data.tostring()
                output = StringIO(data)

                stream = InputIOStream(output, filename=test_file)

                # Create parser
                test_file_unicode = unicodeFilename(test_file)
                try:
                    parser = guessParser(stream)
                except InputStreamError, err:
#                    print "Unable to create parser: %s" % err
                    continue
                if not parser:
#                    print "Unable to create parser"
                    continue

                self.log_error = 0
                metadata = extractMetadata(parser, 0.5)

                if self.log_error:
                    self.nb_error += 1
                    SHA=sha.new(data).hexdigest()
                    ERRNAME="%s-%s" % (SHA, basename(test_file))
                    error_filename = path.join(GOTCHA, ERRNAME)
                    print error_filename
                    open(error_filename, "wb").write(data)
                    unlink_tmp_file = False
                    print "=> ERROR: %s" % ERRNAME
            finally:
                if unlink_tmp_file:
                    unlink(self.tmp_file)

if len(argv) != 2:
    print >>stderr, "usage: %s directory" % argv[0]
    exit(1)

pwd = getcwd()
TEST_FILES=argv[1]
GOTCHA=path.join(pwd, "error")
if False:
    PROG="hachoir-grep --all --quiet"
else:
    PROG="hachoir-metadata --quiet"
MAX_SIZE=5000*512

TEST_FILES = path.expanduser(TEST_FILES)
TEST_FILES = path.normpath(TEST_FILES)

try:
    mkdir(GOTCHA)
except OSError, err:
    if err[0]:
        pass
    else:
        raise

if pwd == TEST_FILES:
    print "ERROR: don't run %s in %s directory (or your files will be removed)" % (
        argv[0], TEST_FILES)
    exit(1)

# Nice
nice(19)

fuzzer = Fuzzer()
try:
    fuzzer.load(TEST_FILES)
    fuzzer.fuzz()
except KeyboardInterrupt:
    print "Stop"

