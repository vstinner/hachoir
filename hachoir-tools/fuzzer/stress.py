#!/usr/bin/env python

from os import path, getcwd, access, R_OK, unlink, nice, mkdir, system, popen4, rename
from os.path import basename
from sys import exit, argv, stderr
from glob import glob
from random import choice as random_choice
from array import array
from cStringIO import StringIO
from hachoir_core.memory import PAGE_SIZE, MemoryLimit
from errno import EEXIST
from time import time, sleep
from hachoir_core.error import HACHOIR_ERRORS
from hachoir_core.log import log as hachoir_logger, Log
from hachoir_core.stream import InputIOStream, InputStreamError
from hachoir_metadata import extractMetadata
from hachoir_parser import guessParser
from mangle import mangle
import re

# Constants
SLEEP_SEC = 0
MAX_SIZE = 1024 * 1024
MAX_DURATION = 10.0
MEMORY_LIMIT = 5 * 1024 * 1024
MANGLE_PERCENT = 0.25

try:
    import sha
    def generateUniqueID(data):
        return sha.new(data).hexdigest()
except ImportError:
    def generateUniqueID(data):
        generateUniqueID.sequence += 1
        return generateUniqueID.sequence
    generateUniqueID.sequence = 0

class Fuzzer:
    def __init__(self, filedb_dirs, error_dir):
        self.filedb_dirs = filedb_dirs
        self.filedb = []
        self.tmp_file = "/tmp/stress-hachoir"
        self.nb_error = 0
        self.error_dir = error_dir
        self.verbose = False

    def filterError(self, text):
        if "Error during metadata extraction" in text:
            return False
        if text.startswith("Error when creating MIME type"):
            return True
        if text.startswith("Unable to create value: "):
            why = text[24:]
            if why.startswith("Can't get field \""):
                return True
            if why.startswith("invalid literal for int(): "):
                return True
            if why.startswith("timestampUNIX(): value have to be in "):
                return True
            if re.match("^Can't read [0-9]+ bits at ", why):
                return True
            if why.startswith("'decimal' codec can't encode character"):
                return True
            if why.startswith("date newer than year "):
                return True
            if why in (
            "day is out of range for month",
            "year is out of range",
            "[Float80] floating point overflow"):
                return True
            if re.match("^(second|minute|hour|month) must be in ", why):
                return True
        if re.match("days=[0-9]+; must have magnitude ", text):
            # Error during metadata extraction: days=1143586582; must have magnitude <= 999999999
            return True
        if "floating point overflow" in text:
            return True
        if "field is too large" in text:
            return True
        if "Seek below field set start" in text:
            return True
        if text.startswith("Unable to create directory directory["):
            # [/section_rsrc] Unable to create directory directory[2][0][]: Can't get field "header" from /section_rsrc/directory[2][0][]
            return True
        if text.startswith("Unable to parse a FAT chain: "):
            # Unable to parse a FAT chain: list index out of range
            return True
        return False

    def newLog(self, level, prefix, text, context):
        if level < Log.LOG_ERROR or self.filterError(text):
            if self.verbose:
                print "   ignore %s %s" % (prefix, text)
            return
        self.log_error += 1
        print "METADATA ERROR: %s %s" % (prefix, text)

    def createStream(self, test_file):
        # Read bytes
        data = open(test_file, "rb").read(MAX_SIZE)
        data = array('B', data)

        # Mangle
        size = len(data)
        count = mangle(data, MANGLE_PERCENT )
        if self.verbose:
            print "   mangle: %.2f%% (%s/%s)" % (
                count * 100.0 / size, count, size)

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
            if self.verbose:
                print "   unable to create parser"
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
        if self.verbose:
            if metadata:
                for line in unicode(metadata).split("\n"):
                    print "   metadata>> %s" % line
            else:
                print "   unable to create metadata"
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
            while True:
                test_file = random_choice(self.filedb)
                print "[+] %s error -- test file: %s" % (self.nb_error, basename(test_file))
                ok = self.fuzzFile(test_file)
                if not ok:
                    break
                if SLEEP_SEC:
                    sleep(SLEEP_SEC)
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

