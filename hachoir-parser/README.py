#!/usr/bin/env python

def main():
    from hachoir_parser.parser_list import HachoirParserList

    # Write header
    for line in open('README.header'):
        line = line.rstrip()
        print line
    if line:
        print

    # Write changelog
    for line in open('ChangeLog'):
        line = line.rstrip()
        print line
    if line:
        print

    # Write parser list
    format = "rest"
    if format == "rest":
        print "Parser list"
        print "==========="
        print
    HachoirParserList().print_(format=format)

if __name__ == "__main__":
    main()

