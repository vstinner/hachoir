from os import path
from os.path import basename
from random import randint
from tools import getFilesize, generateUniqueID
from hachoir_core.stream import InputIOStream, InputStreamError
from hachoir_metadata import extractMetadata
from hachoir_parser import guessParser
from hachoir_core.error import HACHOIR_ERRORS
from cStringIO import StringIO
from array import array
from mangle import mangle
from time import time

# Truncate: minimum/maximum file size (in bytes)
MIN_SIZE = 1
MAX_SIZE = 1024 * 1024

# Limit each test to 10 secondes
MAX_DURATION = 10.0

# Number of mangle operation depending of current size
# '0.30' means: 30% of current size in byte
MANGLE_PERCENT = 0.01
MANGLE_PERCENT_INCR = 0
MIN_MANGLE_PERCENT = 0.10

# Limit fuzzing to 40 tests
MAX_NB_EXTRACT = 40

# 1 times on 20 tries
TRUNCATE_RATE = 20

class UndoMangle:
    def __init__(self, fuzz):
        self.data = fuzz.data.tostring()
        self.orig = fuzz.is_original

    def __call__(self, fuzz):
        fuzz.data = array('B', self.data)
        fuzz.is_original = self.orig

class UndoTruncate:
    def __init__(self, fuzz):
        self.data = fuzz.data
        self.orig = fuzz.is_original

    def __call__(self, fuzz):
        fuzz.data = self.data
        fuzz.is_original = self.orig

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
        self.mangle_call = 0
        size = randint(MIN_SIZE, MAX_SIZE)
        data_str = self.file.read(size)
        self.data = array('B', data_str)
        self.undo = None
        self.nb_extract = 0
        if len(self.data) < self.size:
            self.is_original = False
            self.nb_truncate = 1
            self.warning("Truncate to %s bytes" % len(self.data))
        else:
            self.is_original = True
            self.nb_truncate = 0
            self.info("Size: %s bytes" % len(self.data))

    def acceptTruncate(self):
        return MIN_SIZE < len(self.data)

    def sumUp(self):
        self.warning("[SUMUP] Extraction: %s" % self.nb_extract)
        if self.mangle_call:
            self.warning("[SUMUP] Mangle# %s (%s op.)" % (
                self.mangle_call, self.mangle_count))
        if self.nb_truncate:
            percent = len(self.data) * 100.0 / self.size
            self.warning("[SUMUP] Truncate# %s  -- size: %.1f%% of %s" % (
                self.nb_truncate, percent, self.size))

    def warning(self, message):
        print "    %s (%s): %s" % (basename(self.filename), self.nb_extract, message)

    def info(self, message):
        if self.verbose:
            self.warning(message)

    def mangle(self):
        # Store last state
        self.undo = UndoMangle(self)

        # Mangle data
        count = mangle(self.data, self.mangle_percent)

        # Update state
        self.mangle_call += 1
        self.mangle_count += count
        self.is_original = False
        self.warning("Mangle #%s (%s op.)" % (self.mangle_call, count))

    def truncate(self):
        assert MIN_SIZE < len(self.data)
        #  Store last state (for undo)
        self.undo = UndoTruncate(self)

        # Truncate
        self.nb_truncate += 1
        new_size = randint(MIN_SIZE, len(self.data)-1)
        self.warning("Truncate #%s (%s bytes)" % (self.nb_truncate, new_size))
        self.data = self.data[:new_size]
        self.is_original = False

    def tryUndo(self):
        # No operation to undo?
        if not self.undo:
            self.info("Unable to undo")
            return False

        # Undo
        self.nb_undo += 1
        self.info("Undo #%s" % self.nb_undo)
        self.undo(self)
        self.undo = None

        # Update mangle percent
        percent = max(self.mangle_percent - MANGLE_PERCENT_INCR, MIN_MANGLE_PERCENT)
        if self.mangle_percent != percent:
            self.mangle_percent = percent
            self.info("Set mangle percent to: %u%%" % int(self.mangle_percent*100))
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
        filename = path.join(self.fuzzer.error_dir, filename)
        open(filename, "wb").write(data)
        print "=> Store file %s" % filename

