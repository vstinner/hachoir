#!/usr/bin/env python


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
    HachoirParserList().print_(out, format=format)

def main():
    readme = open('README', 'w')
    writeReadme(readme)
    readme.close()
    print "README updated."

if __name__ == "__main__":
    main()

