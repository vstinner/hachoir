#!/usr/bin/python
from math import log

class Entropy:
    def __init__(self):
        self.frequence = dict( (chr(index), 0) for index in xrange(0, 256) )
        self.count = 0

    def readBytes(self, bytes):
        for byte in bytes:
            self.frequence[byte] = self.frequence[byte] + 1
        self.count += len(bytes)
        return self

    def compute(self):
        h = 0
        for value in self.frequence.itervalues():
            if not value:
                continue
            p_i = float(value) / self.count
            h -= p_i * log(p_i, 2)
        return h

from time import time
from sys import stderr

class EntropyFile(Entropy):
    def __init__(self):
        Entropy.__init__(self)
        self.progress_time = 1.0
        self.buffer_size = 4096

    def displayProgress(self, percent):
        print >>stderr, "Progress: %.1f%%" % percent

    def readStream(self, stream, streamsize=None):
        # Read stream size
        if streamsize is None:
            stream.seek(0, 2)
            streamsize = stream.tell()
        if streamsize <= 0:
            raise ValueError("Empty stream")

        # Read stream content
        stream.seek(0,0)
        next_msg = time() + self.progress_time
        while True:
            if next_msg <= time():
                self.displayProgress(stream.tell() * 100.0 / streamsize)
                next_msg = time() + self.progress_time
            raw = stream.read(self.buffer_size)
            if not raw:
                break
            self.readBytes(raw)
        return self

    def readFile(self, filename):
        stream = open(filename, 'rb')
        self.readStream(stream)
        return self

def main():
    from sys import argv, exit
    if len(argv) != 2:
        print >>stderr, "usage: %s filename" % argv[0]
        exit(1)
    entropy = EntropyFile()
    entropy.readFile(argv[1])
    print "Entropy: %.4f bit/byte" % entropy.compute()
    exit(0)

if __name__ == "__main__":
    main()

