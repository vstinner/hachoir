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
from hachoir_core.memory import getTotalMemory, setMemoryLimit
from errno import EEXIST

from hachoir_core.cmd_line import unicodeFilename
from hachoir_core.log import log as hachoir_logger, Log
from hachoir_core.stream import InputIOStream, InputStreamError
from hachoir_metadata import extractMetadata
from hachoir_parser import guessParser

# Constants
MAX_SIZE = 5000*512

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
    def __init__(self, filedb_dir, error_dir):
        self.filedb_dir = filedb_dir
        self.filedb = []
        self.tmp_file = "/tmp/stress-hachoir"
        self.nb_error = 0
        self.error_dir = error_dir

    def newLog(self, level, prefix, text, context):
        if level < Log.LOG_ERROR:
            return
        if "Can't get field \"" in text:
            return
        if "Unable to create value" in text:
            return
        if "Unable to create value" in text:
            return
        self.log_error += 1
        print "METADATA ERROR: %s %s" % (prefix, text)

    def fuzzFile(self, test_file):
        # Read bytes
        data = open(test_file, "rb").read(MAX_SIZE)
        data = array('B', data)

        # Mangle
        size = len(data)
        mangle(data)

        # Create stream
        data = data.tostring()
        output = StringIO(data)
        stream = InputIOStream(output, filename=test_file)

        # Create parser
        test_file_unicode = unicodeFilename(test_file)
        try:
            parser = guessParser(stream)
        except InputStreamError, err:
            parser = None
        if not parser:
            print "  (unable to create parser)"
            return

        # Extract metadata
        self.log_error = 0
        metadata = extractMetadata(parser, 0.5)

        # Process error (if any)
        if self.log_error:
            self.copyError(test_file, data)

    def copyError(self, test_file, data):
        self.nb_error += 1
        SHA=sha.new(data).hexdigest()
        ERRNAME="%s-%s" % (SHA, basename(test_file))
        error_filename = path.join(self.error_dir, ERRNAME)
        open(error_filename, "wb").write(data)
        print "=> ERROR: %s" % error_filename

    def init(self):
        # Setup log
        self.nb_error=0
        hachoir_logger.use_print = False
        hachoir_logger.on_new_message = self.newLog

        # Load file DB
        self.filedb = glob(path.join(self.filedb_dir, "*.*"))
        if not self.filedb:
            print "Empty directory: %s" % self.filedb_dir
            exit(1)

        # Create error directory
        try:
            mkdir(self.error_dir)
        except OSError, err:
            if err[0] == EEXIST:
                pass

    def run(self):
        self.init()
        while True:
            test_file = random.choice(self.filedb)
            print "total: %s error -- test file: %s" % (self.nb_error, basename(test_file))
            self.fuzzFile(test_file)

def main():
    # Read command line argument
    if len(argv) != 2:
        print >>stderr, "usage: %s directory" % argv[0]
        exit(1)
    TEST_FILES = argv[1]
    TEST_FILES = path.expanduser(TEST_FILES)
    TEST_FILES = path.normpath(TEST_FILES)

    # Directory is current directory?
    err_dir = path.join(getcwd(), "error")

    # Nice
    nice(19)

    fuzzer = Fuzzer(TEST_FILES, err_dir)
    try:
        fuzzer.run()
    except KeyboardInterrupt:
        print "Stop"

if __name__ == "__main__":
    main()
