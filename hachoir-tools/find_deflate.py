#!/usr/bin/python
from zlib import decompress, error as zlib_error
from sys import argv, stderr, exit

MIN_SIZE = 2

def can_deflate(compressed_data):
    try:
        data = decompress(compressed_data)
        return True
    except zlib_error:
        return False


def find_deflate(data):
    for index in xrange(len(data)-MIN_SIZE):
        if can_deflate(data[index:]):
            yield index

def main():
    if len(argv) != 2:
        print >>stderr, "usage: %s filename" % argv[0]
        exit(1)
    found = False
    data = open(argv[1], 'rb').read()
    for offset in find_deflate(data):
        found = True
        print "Offset %s" % offset
    if not found:
        print "No deflate block found"
    exit(0)

if __name__ == "__main__":
    main()

