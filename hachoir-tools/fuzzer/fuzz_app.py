#!/usr/bin/env python
from os import nice, mkdir, path, unlink, listdir
from application import Application
from array import array
from mangle import mangle
from time import sleep
from md5 import md5
from sys import argv, exit, stderr
from random import randint
from hachoir_core.timeout import limitedTime, Timeout
from tools import ConfigParser

def cleanupDir(dirname):
    try:
        files=listdir(dirname)
    except OSError:
        return
    for file in files:
        filename = path.join(dirname, file)
        unlink(filename)

class Fuzzer:
    def __init__(self, config, original):
        self.original = original
        self.data = open(self.original, 'rb').read()
        self.program = config.get('application', 'program')
        self.timeout = config.getfloat('application', 'timeout')
        self.tmp_dir = config.get('application', 'tmp_dir')
        assert 1 <= len(self.data)

    def fuzzFile(self, filename):
        app = Application(self.program, filename)
        app.start()
        try:
            limitedTime(self.timeout, app.wait)
        except Timeout:
            print "Timeout error!"
            app.stop()
            return True
        except KeyboardInterrupt:
            print "Interrupt!"
            app.stop()
            return True
        return app.exit_failure and app.exit_code is None

    def info(self, message):
        if False:
            print message

    def warning(self, message):
        print "WARN: %s" % message

    def mangle(self, filename):
        self.info("Mangle")
        data = array('B', self.data)

        if randint(0, 10) == 0:
            size = randint(1, len(self.data)-1)
            print "@@ Truncate to %s bytes" % size
            data = data[:size]

        percent = 30 / 100.0
        count = mangle(data, percent)
        self.warning("Mangle: %s" % count)
        self.info("Output MD5: %s" % md5(data).hexdigest())

        self.info("Write to %s" % filename)
        output = open(filename, 'wb')
        data = data.tofile(output)
        output.close()


    def run(self):
        ext = self.original[-4:]
        MULTIPLE = False
        if MULTIPLE:
            dir = path.join(self.tmp_dir, "fuzz.clamav")
        else:
            tmp_name = path.join(self.tmp_dir, 'fuzz_app.file%s' % ext)
        try:
            if MULTIPLE:
                cleanupDir(dir)
                try:
                    mkdir(dir)
                except OSError:
                    pass
            while True:
                if MULTIPLE:
                    files = []
                    for index in xrange(50):
                        tmp_name = path.join(dir, 'image.%u.%s' % (index, ext))
                        self.mangle(tmp_name)
                        files.append(tmp_name)
                else:
                    self.mangle(tmp_name)
                    files = [tmp_name]

                print "============= Run Test ==============="
                if self.fuzzFile(files):
                    print "Fuzzing error: stop!"
                    break
                print "Test: ok"
                if MULTIPLE:
                    break
        except KeyboardInterrupt:
            print "Interrupt."

def main():
    global config

    # Read arguments
    if len(argv) != 3:
        print >>stderr, "usage: %s config.cfg filename" % argv[0]
        exit(1)
    config_file = argv[1]
    config = ConfigParser()
    config.read(["defaults.cfg", config_file])
    document = argv[2]

    # Be nice with CPU
    nice(19)

    # Run fuzzer
    fuzzer = Fuzzer(config, document)
    fuzzer.run()

if __name__ == "__main__":
    main()

