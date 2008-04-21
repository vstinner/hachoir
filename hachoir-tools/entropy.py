#!/usr/bin/python
from math import log
from sys import exit, argv, stderr
from time import time

BUFFER_SIZE = 4096

def entropyFile(filename):
    stream = open(filename, 'rb')
    stream.seek(0,2)
    filesize = stream.tell()
    if filesize == 0:
        print >>stderr, "Empty file"
        exit(1)
    print >>stderr, "Filesize: %s bytes" % filesize
    stream.seek(0,0)
    return entropyStream(stream, filesize)

def entropyStream(stream, streamsize):
    if streamsize <= 0:
        raise ValueError("Empty stream")
    # Create list of
    count = {}
    for i in range(0, 256):
        count[ chr(i) ] = 0
    p = []
    stream.seek(0)
    n = 0
    next_msg = time() + 1.0
    while True:
        lastpos = stream.tell()
        raw = stream.read(BUFFER_SIZE)
        if not raw:
            break
        if next_msg <= time():
            percent = lastpos * 100.0 / streamsize
            print >>stderr, "Progress: %.1f%%" % percent
            next_msg = time() + 1.0
        n += len(raw)
        for i in raw:
            count[i] = count[i] + 1
    h = 0
    for i in range(0, 256):
        i = chr(i)
        if count[i] != 0:
            p_i = float(count[i]) / streamsize
            h -= p_i * log(p_i, 2)
    return h

def main():
    if len(argv) != 2:
        print >>stderr, "usage: %s filename" % argv[0]
        exit(1)
    value = entropyFile(argv[1])
    print "Entropy: %.4f bit/byte" % value
    exit(0)

if __name__ == "__main__":
    main()

