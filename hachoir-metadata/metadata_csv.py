#!/usr/bin/env python
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
from hachoir_core.i18n import initLocale, getTerminalCharset
from sys import argv, stderr, exit
from os import walk
from os.path import join as path_join
from fnmatch import fnmatch
from datetime import datetime
import codecs

OUTPUT_FILENAME = "metadata.csv"

def processFile(counter, filename, charset, output):
    filename, realname = unicodeFilename(filename), filename
    print u"[%s] Process file %s..." % (counter, filename)
    parser = createParser(filename, realname)
    if not parser:
        print >>stderr, "Unable to parse file"
        return False
    try:
        metadata = extractMetadata(parser)
    except HachoirError, err:
        print >>stderr, "Metadata extraction error: %s" % unicode(err)
        return False
    if not metadata:
        print >>stderr, "Unable to extract metadata"
        return False

    title = metadata.get('title', '')
    creation = metadata.get('creation_date', datetime(1970, 1, 1))
    author = metadata.get('author', '')

    filename = makePrintable(filename, charset, to_unicode=True)
    title = makePrintable(title, charset, to_unicode=True)
    print >>output, u"%s; %s; %s; %s" % (filename, title, creation, author)
    return True

def findFiles(directory, pattern):
    for dirpath, dirnames, filenames in walk(directory):
        for filename in filenames:
            if not fnmatch(filename.lower(), pattern):
                continue
            yield path_join(dirpath, filename)

def main():
    initLocale()
    if len(argv) != 2:
        print >>stderr, "usage: %s directory" % argv[0]
        exit(1)
    directory = argv[1]

    charset = "UTF-8"
    output = codecs.open(OUTPUT_FILENAME, "w", charset)
    total = 0
    invalid = 0
    for filename in findFiles(directory, '*.doc'):
        total += 1
        ok = processFile(total, filename, charset, output)
        if not ok:
            invalid += 1
    output.close()

    print
    print "Valid files: %s" % (total - invalid)
    print "Invalid files: %s" % invalid
    print "Total files: %s" % total
    print
    print "Result written into %s" % OUTPUT_FILENAME

if __name__ == "__main__":
    main()

