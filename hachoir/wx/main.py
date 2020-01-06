#!/usr/bin/env python3

from hachoir.wx.app import app_t
from hachoir import __version__
from hachoir.core.cmd_line import getHachoirOptions, configureHachoir
from optparse import OptionParser
import sys


def parseOptions():
    parser = OptionParser(usage="%prog [options] [filename]")
    hachoir = getHachoirOptions(parser)
    parser.add_option_group(hachoir)

    values, arguments = parser.parse_args()
    if len(arguments) == 1:
        filename = arguments[0]
    elif not arguments:
        filename = None
    else:
        parser.print_help()
        sys.exit(1)
    return values, filename


def main():
    print("hachoir version %s" % __version__)
    print()
    values, filename = parseOptions()
    configureHachoir(values)
    app = app_t(filename)
    app.MainLoop()


if __name__ == '__main__':
    main()
