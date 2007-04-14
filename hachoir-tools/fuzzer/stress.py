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
MANGLE_PERCENT = 0.30
MAX_NB_UNDO = 10
MIN_MANGLE_PERCENT = 0.01
MANGLE_PERCENT_INCR = float(MANGLE_PERCENT - MIN_MANGLE_PERCENT) / MAX_NB_UNDO
MAX_NB_TRUNCATE = 5

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

class FileFuzzerUndo:
    def __init__(self):
        self.mangle_count = 0
        self.nb_truncate = 0
        self.reset()

    def reset(self):
        self.data = None

class FileFuzzer:
    def __init__(self, fuzzer, filename):
        self.fuzzer = fuzzer
        self.verbose = fuzzer.verbose
        self.mangle_percent = MANGLE_PERCENT
        self.file = open(filename, "rb")
        self.nb_undo = 0
        self.filename = filename
        self.size = getFilesize(self.file)
        self.mangle_count = 0
        self.nb_truncate = 0
        size = randint(MIN_SIZE, MAX_SIZE)
        data_str = self.file.read(size)
        self.data = array('B', data_str)
        self.truncated = len(self.data) < self.size
        self.undo_state = FileFuzzerUndo()
        self.nb_extract = 0
        if self.truncated:
            self.warning("Truncate to %s bytes" % len(self.data))
        else:
            self.info("Size: %s bytes" % len(self.data))
        self.accept_truncate = True

    def acceptTruncate(self):
        return (self.nb_truncate < MAX_NB_TRUNCATE) and (1 < len(self.data))

    def sumUp(self):
        print "Extract: %s; size: %.1f%% of %s; mangle: %s" % (
            self.nb_extract, len(self.data)*100.0/self.size,
            self.size, self.mangle_count)

    def warning(self, message):
        print "[%s] %s" % (basename(self.filename), message)

    def info(self, message):
        if self.verbose:
            self.warning(message)

    def mangle(self):
        # Store last state
        self.undo_state.data = self.data.tostring()
        self.undo_state.mangle_count = self.mangle_count

        # Mangle data
        count = mangle(self.data, self.mangle_percent)

        # Update state
        self.mangle_count += count
        self.info("Mangle: %s operations (+%s)" % (self.mangle_count, count))

    def truncate(self):
        assert 1 < len(self.data)
        #  Store last state (for undo)
        self.undo_state.data = self.data.tostring()
        self.undo_state.nb_truncate = self.nb_truncate
        self.nb_truncate += 1

        # Truncate
        new_size = randint(1, len(self.data)-1)
        self.warning("Truncate to %s bytes" % new_size)
        self.data = self.data[:new_size]
        self.truncated = True

    def tryUndo(self):
        if not self.undo_state.data:
            self.info("Unable to undo")
            return False
        self.nb_undo += 1

#        self.accept_truncate = False
        percent = max(self.mangle_percent - MANGLE_PERCENT_INCR, MIN_MANGLE_PERCENT)
        if self.mangle_percent != percent:
            self.mangle_percent = percent
            self.info("Set mangle percent to: %u%%" % int(self.mangle_percent*100))
        self.data = array('B', self.undo_state.data)
        self.mangle_count = self.undo_state.mangle_count
        self.nb_truncate = self.undo_state.nb_truncate
        self.undo_state.reset()

        self.warning("Undo! %u/%u" % (self.nb_undo, MAX_NB_UNDO))
        return True

    def extract(self):
        self.nb_extract += 1
        self.prefix = ""

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
        try:
            metadata = extractMetadata(parser, 0.5, False)
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
        if not failure and (metadata is None or not metadata):
            self.info("Unable to extract metadata")
            return None
#        for line in metadata.exportPlaintext():
#            print ">>> %s" % line
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
        if "FAT chain: " in text:
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
                prefix = fuzz.prefix
            except KeyboardInterrupt:
                try:
                    failure = (raw_input("Keep current file (y/n)?").strip() == "y")
                except (KeyboardInterrupt, EOFError):
                    print
                    failure = False
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
            if fatal_error:
                break
            if failure is None \
            and fuzz.nb_undo < MAX_NB_UNDO:
                if fuzz.tryUndo():
                    continue
            if failure is None:
                return True
            if failure:
                break
            if fuzz.acceptTruncate():
                if randint(0,10) == 0:
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

