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
    print "Parser list"
    print "==========="
    print
    HachoirParserList().print_(format="rest")

if __name__ == "__main__":
    main()

