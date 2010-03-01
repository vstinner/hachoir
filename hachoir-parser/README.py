#!/usr/bin/env python
from __future__ import with_statement

def writeReadme(out):
    from hachoir_parser.parser_list import HachoirParserList

    # Write header
    for line in open('README.header'):
        line = line.rstrip()
        print >>out, line
    if line:
        print >>out

    # Write changelog
    for line in open('ChangeLog'):
        line = line.rstrip()
        print >>out, line
    if line:
        print >>out

    # Write parser list
    format = "rest"
    if format == "rest":
        print >>out, "Parser list"
        print >>out, "==========="
        print >>out
    HachoirParserList().print_(out=out, format=format)

def main():
    with open('README', 'w') as readme:
        writeReadme(readme)
    print "README updated."

if __name__ == "__main__":
    main()

