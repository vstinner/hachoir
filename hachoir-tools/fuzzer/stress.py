#!/usr/bin/env python

from os import path, getcwd, access, R_OK, unlink, nice, mkdir, system, popen4, rename
from os.path import basename
from sys import exit, argv, stderr
from glob import glob
import random
from random import randint
from array import array
from cStringIO import StringIO
from hachoir_core.memory import PAGE_SIZE, MemoryLimit
from errno import EEXIST
from time import time
from hachoir_core.error import HACHOIR_ERRORS
from hachoir_core.log import log as hachoir_logger, Log
from hachoir_core.stream import InputIOStream, InputStreamError
from hachoir_metadata import extractMetadata
from hachoir_parser import guessParser

try:
    import sha
    def generateUniqueID(data):
        return sha.new(data).hexdigest()
except ImportError:
    def generateUniqueID(data):
        generateUniqueID.sequence += 1
        return generateUniqueID.sequence
    generateUniqueID.sequence = 0

# Constants
MAX_SIZE = 5000*512
MAX_DURATION = 2.0
MEMORY_LIMIT = PAGE_SIZE * 100

def mangle(data):
    hsize = len(data)-1
    max_count = min(hsize // 25, 250)
    max_count = max(max_count, 4)
    count = randint(1, max_count)
    for index in xrange(count):
        off = randint(0, hsize)
        data[off] = randint(0, 255)

class Fuzzer:
    def __init__(self, filedb_dirs, error_dir):
        self.filedb_dirs = filedb_dirs
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
        if "field is too large" in text:
            return
        self.log_error += 1
        print "METADATA ERROR: %s %s" % (prefix, text)

    def createStream(self, test_file):
        # Read bytes
        data = open(test_file, "rb").read(MAX_SIZE)
        data = array('B', data)

        # Mangle
        size = len(data)
        mangle(data)

        # Create stream
        data = data.tostring()
        output = StringIO(data)
        return data, InputIOStream(output, filename=test_file)

    def fuzzStream(self, stream):
        # Create parser
        start = time()
        try:
            parser = guessParser(stream)
        except InputStreamError, err:
            parser = None
        if not parser:
            print "  (unable to create parser)"
            return False, ""

        # Extract metadata
        self.log_error = 0
        prefix = ""
        try:
            metadata = extractMetadata(parser, 0.5)
            failure = bool(self.log_error)
        except (HACHOIR_ERRORS, AssertionError), err:
            print "SERIOUS ERROR: %s" % err
            failure = True
        duration = time() - start

        # Timeout?
        if MAX_DURATION < duration:
            print "Process is too long: %.1f seconds" % duration
            failure = True
            prefix = "timeout"
        return failure, prefix

    def fuzzFile(self, test_file):
        data, stream = self.createStream(test_file)

        fatal_error = False
        try:
            limiter = MemoryLimit(MEMORY_LIMIT)
            failure, prefix = limiter.call(self.fuzzStream, stream)
        except KeyboardInterrupt:
            failure = True
            prefix = "interrupt"
            fatal_error = True
        except MemoryError:
            print "MEMORY ERROR!"
            failure = True
            prefix = "memory"

        # Process error
        if failure:
            self.copyError(test_file, data, prefix)
        return (not fatal_error)

    def copyError(self, test_file, data, prefix):
        self.nb_error += 1
        uniq_id = generateUniqueID(data)
        ERRNAME="%s-%s" % (uniq_id, basename(test_file))
        if prefix:
            ERRNAME = "%s-%s" % (prefix, ERRNAME)
        error_filename = path.join(self.error_dir, ERRNAME)
        open(error_filename, "wb").write(data)
        print "=> Store file %s" % ERRNAME

    def init(self):
        # Setup log
        self.nb_error=0
        hachoir_logger.use_print = False
        hachoir_logger.on_new_message = self.newLog

        # Load file DB
        self.filedb = []
        for directory in self.filedb_dirs:
            new_files = glob(path.join(directory, "*.*"))
            self.filedb.extend(new_files)
        if not self.filedb:
            print "Empty directories: %s" % self.filedb_dirs
            exit(1)

        # Create error directory
        try:
            mkdir(self.error_dir)
        except OSError, err:
            if err[0] == EEXIST:
                pass

    def run(self):
        self.init()
        try:
            ok = True
            while ok:
                test_file = random.choice(self.filedb)
                print "total: %s error -- test file: %s" % (self.nb_error, basename(test_file))
                ok = self.fuzzFile(test_file)
        except KeyboardInterrupt:
            print "Stop"

def main():
    # Read command line argument
    if len(argv) < 2:
        print >>stderr, "usage: %s directory [directory2 ...]" % argv[0]
        exit(1)
    test_dirs = [ path.normpath(path.expanduser(item)) for item in argv[1:] ]

    # Directory is current directory?
    err_dir = path.join(getcwd(), "error")

    # Nice
    nice(19)

    fuzzer = Fuzzer(test_dirs, err_dir)
    fuzzer.run()

if __name__ == "__main__":
    main()
