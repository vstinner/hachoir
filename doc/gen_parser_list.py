#!/usr/bin/env python3
import os.path

def writeReadme(out):
    from hachoir.parser.parser_list import HachoirParserList

    # Write parser list
    format = "rest"
    if format == "rest":
        print("Parser list", file=out)
        print("===========", file=out)
        print(file=out)
    HachoirParserList().print_(out=out, format=format)

def main():
    path = os.path.dirname(__file__)
    filename = os.path.join(path, 'parser_list.rst')
    with open(filename, 'w') as readme:
        writeReadme(readme)
    print("%s regenerated" % filename)

if __name__ == "__main__":
    main()

