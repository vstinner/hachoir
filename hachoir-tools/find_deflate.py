#!/usr/bin/python
from zlib import decompress, error as zlib_error
from sys import argv, stderr, exit
from time import time

MIN_SIZE = 2

def canDeflate(compressed_data):
    try:
        data = decompress(compressed_data)
        return True
    except zlib_error:
        return False

def findDeflateBlocks(data):
    next_msg = time() + 1.0
    max_index = len(data)-MIN_SIZE-1
    for index in xrange(max_index+1):
        if next_msg < time():
            next_msg = time() + 1.0
            print "Progress: %.1f%% (offset %s/%s)" % (
                index*100.0/max_index, index, max_index)
        if canDeflate(data[index:]):
            yield index

def guessDeflateSize(data, offset):
    size = len(data)-offset
    while size:
        if canDeflate(data[offset:offset+size]):
            yield size
        size -= 1

def main():
    if len(argv) != 2:
        print >>stderr, "usage: %s filename" % argv[0]
        exit(1)
    data = open(argv[1], 'rb').read()
    offsets = []
    for offset in findDeflateBlocks(data):
        print "Offset %s" % offset
        offsets.append(offset)
    if offsets:
        for offset in offsets:
            for size in guessDeflateSize(data, offset):
                if size == (len(data) - offset):
                    size = "%s (until the end)" % size
                print "Offset %s -- size %s" % (offset, size)
    else:
        print >>stderr, "No deflate block found"
    exit(0)

if __name__ == "__main__":
    main()

