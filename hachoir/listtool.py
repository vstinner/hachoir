#
# Tool for parsing a file and writing all fields to stdout.
#

from hachoir.core.cmd_line import getHachoirOptions, configureHachoir
from hachoir.core.cmd_line import displayVersion
from hachoir.stream import InputStreamError, FileInputStream
from hachoir.parser import guessParser, HachoirParserList
from optparse import OptionGroup, OptionParser
import sys


def printFieldSet(field_set, args, options={}):
    pass


def displayParserList(*args):
    HachoirParserList().print_()
    sys.exit(0)


def parseOptions():
    parser = OptionParser(usage="%prog [options] filename")

    common = OptionGroup(parser, "List Tool", "Options of list tool")
    common.add_option("--parser", help="Use the specified parser (use its identifier)",
                      type="str", action="store", default=None)
    common.add_option("--offset", help="Skip first bytes of input file",
                      type="long", action="store", default=0)
    common.add_option("--parser-list", help="List all parsers then exit",
                      action="callback", callback=displayParserList)
    common.add_option("--size", help="Maximum size of bytes of input file",
                      type="long", action="store", default=None)
    common.add_option("--hide-value", dest="display_value", help="Don't display value",
                      action="store_false", default=True)
    common.add_option("--hide-size", dest="display_size", help="Don't display size",
                      action="store_false", default=True)
    common.add_option("--version", help="Display version and exit",
                      action="callback", callback=displayVersion)
    parser.add_option_group(common)

    hachoir = getHachoirOptions(parser)
    parser.add_option_group(hachoir)

    values, arguments = parser.parse_args()
    if len(arguments) != 1:
        parser.print_help()
        sys.exit(1)
    return values, arguments[0]


def openParser(parser_id, filename, offset, size):
    tags = []
    if parser_id:
        tags += [("id", parser_id), None]
    try:
        stream = FileInputStream(filename,
                                 offset=offset, size=size, tags=tags)
    except InputStreamError as err:
        return None, "Unable to open file: %s" % err
    parser = guessParser(stream)
    if not parser:
        return None, "Unable to parse file: %s" % filename
    return parser, None


def main():
    # Parse options and initialize Hachoir
    values, filename = parseOptions()
    configureHachoir(values)

    # Open file and create parser
    parser, err = openParser(values.parser, filename,
                             values.offset, values.size)
    if err:
        print(err)
        sys.exit(1)

    # Explore file
    with parser:
        printFieldSet(parser, values, {
            "display_size": values.display_size,
            "display_value": values.display_value,
        })


if __name__ == "__main__":
    main()
