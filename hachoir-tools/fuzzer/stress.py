#!/usr/bin/env python

from os import path, getcwd, access, R_OK, unlink, nice, mkdir, system, popen4, rename
from os.path import basename
from sys import exit, argv, stderr
from glob import glob
from random import choice as random_choice, randint
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
MIN_SIZE = 1
MAX_SIZE = 1024 * 1024
MAX_DURATION = 10.0
MEMORY_LIMIT = 5 * 1024 * 1024
MANGLE_PERCENT = 0.10

try:
    import sha
    def generateUniqueID(data):
        return sha.new(data).hexdigest()
except ImportError:
    def generateUniqueID(data):
        generateUniqueID.sequence += 1
        return generateUniqueID.sequence
    generateUniqueID.sequence = 0

def getFilesize(file):
    file.seek(0, 2)
    size = file.tell()
    file.seek(0, 0)
    return size

class FileFuzzer:
    def __init__(self, fuzzer, filename):
        self.fuzzer = fuzzer
        self.verbose = fuzzer.verbose
        self.file = open(filename, "rb")
        self.filename = filename
        self.size = getFilesize(self.file)
        self.mangle_count = 0
        size = randint(MIN_SIZE, MAX_SIZE)
        data_str = self.file.read(size)
        self.data = array('B', data_str)
        self.truncated = len(self.data) < self.size
        self.nb_extract = 0
        if self.truncated:
            self.info("Truncate to %s bytes" % len(self.data))
        else:
            self.info("Size: %s bytes" % len(self.data))
            self.mangle()

    def sumUp(self):
        print "Extract: %s; size: %.1f%%; mangle: %s" % (
            self.nb_extract, len(self.data)*100.0/self.size, self.mangle_count)

    def info(self, message):
        if not self.verbose:
            return
        print "[%s] %s" % (basename(self.filename), message)

    def mangle(self):
        count = mangle(self.data, MANGLE_PERCENT)
        self.mangle_count += count
        self.info("Mangle: %s operations (+%s)"
            % (self.mangle_count, count))

    def truncate(self):
        assert 1 < len(self.data)
        new_size = randint(1, len(self.data)-1)
        self.info("Truncate to %s bytes" % new_size)
        self.data = self.data[:new_size]
        self.truncated = True

    def extract(self):
        self.nb_extract += 1
        data = self.data.tostring()
        stream = InputIOStream(StringIO(data), filename=self.filename)

        # Create parser
        start = time()
        try:
            parser = guessParser(stream)
        except InputStreamError, err:
            parser = None
        if not parser:
            self.info("Unable to create parser: stop")
            return None

        # Extract metadata
        self.prefix = ""
        try:
            metadata = extractMetadata(parser, 0.5)
            failure = bool(self.fuzzer.log_error)
        except (HACHOIR_ERRORS, AssertionError), err:
            self.info("SERIOUS ERROR: %s" % err)
            self.prefix = "metadata"
            failure = True
        duration = time() - start

        # Timeout?
        if MAX_DURATION < duration:
            self.info("Process is too long: %.1f seconds" % duration)
            failure = True
            self.prefix = "timeout"
        if not failure and metadata is None:
            self.info("Unable to extract metadata")
            return None
        return failure

    def keepFile(self, prefix):
        data = self.data.tostring()
        uniq_id = generateUniqueID(data)
        filename="%s-%s" % (uniq_id, basename(self.filename))
        if prefix:
            filename = "%s-%s" % (prefix, filename)
        error_filename = path.join(self.fuzzer.error_dir, filename)
        open(error_filename, "wb").write(data)
        print "=> Store file %s" % filename

class Fuzzer:
    def __init__(self, filedb_dirs, error_dir):
        self.filedb_dirs = filedb_dirs
        self.filedb = []
        self.tmp_file = "/tmp/stress-hachoir"
        self.nb_error = 0
        self.error_dir = error_dir
        self.verbose = True

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
        if "Loop in FAT chain" in text:
            return True
        if text.startswith("Unable to create directory directory["):
            # [/section_rsrc] Unable to create directory directory[2][0][]: Can't get field "header" from /section_rsrc/directory[2][0][]
            return True
        if text.startswith("Unable to parse a FAT chain: "):
            # Unable to parse a FAT chain: list index out of range
            return True
        if text.startswith("EXE resource: depth too high"):
            return True
        if "OLE2: Too much sections" in text:
            return True
        if "OLE2: Invalid endian value" in text:
            return True
        if "Seek above field set end" in text:
            return True
        return False

    def newLog(self, level, prefix, text, context):
        if level < Log.LOG_ERROR or self.filterError(text):
#            if self.verbose:
#                print "   ignore %s %s" % (prefix, text)
            return
        self.log_error += 1
        print "METADATA ERROR: %s %s" % (prefix, text)

    def fuzzFile(self, fuzz):
        limiter = MemoryLimit(MEMORY_LIMIT)

        failure = False
        while True:
            self.log_error = 0
            fatal_error = False
            try:
                failure = limiter.call(fuzz.extract)
                if failure is None:
                    return True
                prefix = fuzz.prefix
            except KeyboardInterrupt:
                try:
                    failure = (raw_input("Keep current file (y/n)?").strip() == "y")
                except (KeyboardInterrupt, EOFError):
                    failure = True
                prefix = "interrupt"
                fatal_error = True
            except MemoryError:
                print "MEMORY ERROR!"
                failure = True
                prefix = "memory"
            except Exception, err:
                print "EXCEPTION (%s): %s" % (err.__class__.__name__, err)
                failure = True
                prefix = "exception"
            if failure or fatal_error:
                break
            if 1 < len(fuzz.data):
                if randint(0,20) == 0:
                    fuzz.truncate()
                else:
                    fuzz.mangle()
            else:
                fuzz.mangle()

        # Process error
        if failure:
            fuzz.keepFile(prefix)
            self.nb_error += 1
        return (not fatal_error)

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
                fuzz = FileFuzzer(self, test_file)
                ok = self.fuzzFile(fuzz)
                fuzz.sumUp()
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

