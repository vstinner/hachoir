#!/usr/bin/env python
from hachoir_core.error import HachoirError
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser
from hachoir_core.tools import makePrintable
from hachoir_metadata import extractMetadata
from hachoir_core.i18n import initLocale
from sys import argv, stderr, exit
from os import walk
from os.path import join as path_join
from fnmatch import fnmatch
import codecs

OUTPUT_FILENAME = "metadata.csv"

class Extractor:
    def __init__(self, directory, fields):
        self.directory = directory
        self.fields = fields
        self.charset = "UTF-8"
        self.total = 0
        self.invalid = 0

    def main(self):
        output = codecs.open(OUTPUT_FILENAME, "w", self.charset)
        for filename in self.findFiles(self.directory, '*.doc'):
            self.total += 1
            line = self.processFile(filename)
            if line:
                print >>output, line
            else:
                self.invalid += 1
        output.close()
        self.summary()

    def summary(self):
        print >>stderr
        print >>stderr, "Valid files: %s" % (self.total - self.invalid)
        print >>stderr, "Invalid files: %s" % self.invalid
        print >>stderr, "Total files: %s" % self.total
        print >>stderr
        print >>stderr, "Result written into %s" % OUTPUT_FILENAME

    def findFiles(self, directory, pattern):
        for dirpath, dirnames, filenames in walk(directory):
            for filename in filenames:
                if not fnmatch(filename.lower(), pattern):
                    continue
                yield path_join(dirpath, filename)

    def processFile(self, filename):
        filename, realname = unicodeFilename(filename), filename
        print u"[%s] Process file %s..." % (self.total, filename)
        parser = createParser(filename, realname)
        if not parser:
            print >>stderr, "Unable to parse file"
            return None
        try:
            metadata = extractMetadata(parser)
        except HachoirError, err:
            print >>stderr, "Metadata extraction error: %s" % unicode(err)
            return None
        if not metadata:
            print >>stderr, "Unable to extract metadata"
            return None

        filename = makePrintable(filename, self.charset, to_unicode=True)
        line = [filename]
        for field in self.fields:
            value = metadata.getText(field, u'')
            value = makePrintable(value, self.charset, to_unicode=True)
            line.append(value)
        return '; '.join(line)

def main():
    initLocale()
    if len(argv) != 3:
        print >>stderr, "usage: %s directory fields" % argv[0]
        print >>stderr
        print >>stderr, "eg. %s . title,creation_date" % argv[0]
        exit(1)
    directory = argv[1]
    fields = [field.strip() for field in argv[2].split(",")]
    Extractor(directory, fields).main()

if __name__ == "__main__":
    main()

