#!/usr/bin/env python3


def writeReadme(out):
    from hachoir.parser.parser_list import HachoirParserList

    # Write header
    for line in open('README.header'):
        line = line.rstrip()
        print(line, file=out)
    if line:
        print(file=out)

    # Write changelog
    for line in open('ChangeLog'):
        line = line.rstrip()
        print(line, file=out)
    if line:
        print(file=out)

    # Write parser list
    format = "rest"
    if format == "rest":
        print("Parser list", file=out)
        print("===========", file=out)
        print(file=out)
    HachoirParserList().print_(out=out, format=format)

def main():
    with open('README', 'w') as readme:
        writeReadme(readme)
    print("README updated.")

if __name__ == "__main__":
    main()

