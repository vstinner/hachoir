#!/usr/bin/env python
from os import path, getcwd, nice, mkdir
from sys import exit, argv, stderr
from glob import glob
from random import choice as random_choice, randint
from hachoir_core.memory import limitedMemory
from errno import EEXIST
from time import sleep
from hachoir_core.log import log as hachoir_logger, Log
from file_fuzzer import FileFuzzer, MAX_NB_EXTRACT, TRUNCATE_RATE
import re

# Constants
SLEEP_SEC = 0
MEMORY_LIMIT = 5 * 1024 * 1024

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
        if "OLE2: Unable to parse property of type" in text:
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

        failure = False
        while fuzz.nb_extract < MAX_NB_EXTRACT:
            if SLEEP_SEC:
                sleep(SLEEP_SEC)
            self.log_error = 0
            fatal_error = False
            try:
                failure = limitedMemory(MEMORY_LIMIT, fuzz.extract)
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
            if failure is None:
                if fuzz.tryUndo():
                    failure = False
                elif fuzz.is_original:
                    print "    Warning: Unsupported file format: remove %s from test suite" % fuzz.filename
                    self.filedb.remove(fuzz.filename)
                    return True
            if failure is None:
                break
            if failure:
                break
            if fuzz.acceptTruncate():
                if randint(0,TRUNCATE_RATE-1) == 0:
                    fuzz.truncate()
                else:
                    fuzz.mangle()
            else:
                fuzz.mangle()

        # Process error
        if failure:
            fuzz.keepFile(prefix)
            self.nb_error += 1
        fuzz.sumUp()
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
                print "[+] %s error -- test file: %s" % (self.nb_error, test_file)
                fuzz = FileFuzzer(self, test_file)
                ok = self.fuzzFile(fuzz)
                if not ok:
                    break
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

