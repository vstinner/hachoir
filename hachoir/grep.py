from hachoir.core.i18n import getTerminalCharset
from hachoir.core.cmd_line import getHachoirOptions, configureHachoir
from hachoir.field import isString
from hachoir.core.benchmark import Benchmark
from hachoir.core.error import error
from hachoir.stream import InputStreamError
from hachoir.core.tools import makePrintable
from hachoir.parser import createParser
from hachoir.core.cmd_line import displayVersion
from optparse import OptionGroup, OptionParser
import errno
import sys


def countChildren(field_set):
    count = 0
    for field in field_set.fields.values:
        if field.is_field_set:
            count += countChildren(field)
        count += 1
    return count


def displayParserStat(parser):
    print("Parser: %s children"
          % countChildren(parser))


def parseOptions():
    parser = OptionParser(usage="%prog [options] "
                                "pattern filename [filename2 ...]")

    common = OptionGroup(parser, "Grep", "Option of grep")
    common.add_option("--percent", help="Display percent",
                      action="store_true", default=False)
    common.add_option("--no-addr", help="Don't display address",
                      action="store_true", default=False)
    common.add_option("--no-value", help="Don't display value",
                      action="store_true", default=False)
    common.add_option("--case", help="Search is case sensitive",
                      action="store_true", default=False)
    common.add_option("--path", help="Display path",
                      action="store_true", default=False)
    common.add_option("--all", help="Match all (just extract strings)",
                      action="store_true", default=False)
    common.add_option("--bench", help="Run benchmark",
                      action="store_true", default=False)
    common.add_option("--version", help="Display version and exit",
                      action="callback", callback=displayVersion)
    parser.add_option_group(common)

    hachoir = getHachoirOptions(parser)
    parser.add_option_group(hachoir)

    values, arguments = parser.parse_args()
    if values.all or values.bench:
        if len(arguments) < 1:
            parser.print_help()
            sys.exit(1)
        pattern = None
        filenames = arguments
    else:
        if len(arguments) < 2:
            parser.print_help()
            sys.exit(1)
        pattern = str(arguments[0], "ascii")
        filenames = arguments[1:]
    return values, pattern, filenames


class Grep:

    def __init__(self):
        self.pattern = None
        self.case_sensitive = True

    def grep(self, fieldset):
        for field in fieldset:
            if field.is_field_set:
                self.grep(field)
                field.reset()
            elif isString(field) and self.match(field):
                self.onMatch(field)

    def match(self, field):
        value = field.value
        if len(value) == 0:
            return False
        if not self.pattern:
            return True
        if not self.case_sensitive:
            value = value.lower()
        return self.pattern in value

    def onMatch(self, field):
        raise NotImplementedError()


class ConsoleGrep(Grep):

    def __init__(self):
        Grep.__init__(self)
        self.term_charset = getTerminalCharset()
        self.display = True
        self.display_filename = True
        self.display_address = True
        self.display_value = True
        self.display_path = False
        self.display_percent = False
        self.filename = None

    def onMatch(self, field):
        if not self.display:
            return
        text = []
        if self.display_percent or self.display_address:
            addr = field.absolute_address
        if self.display_filename:
            filename = makePrintable(self.filename, self.term_charset)
            text.append(filename)
        if self.display_address:
            if (addr % 8) == 0:
                text.append(str(addr // 8))
            else:
                text.append("%u.%u" % (addr // 8, addr % 8))
        if self.display_path:
            text.append(field.path)
        if self.display_value:
            value = field.value
            value = makePrintable(value, self.term_charset)
            text.append(value)
        if not text:
            return
        text = ":".join(text)
        if self.display_percent:
            percent = float(addr) * 100 / field.parent.root.size
            sys.stdout.flush()
            sys.stderr.write("[%02.1f%%] " % percent)
            sys.stderr.flush()
        print(text)

    def searchFile(self, filename, pattern, case_sensitive=True):
        self.filename = filename
        self.case_sensitive = case_sensitive
        if pattern and not self.case_sensitive:
            pattern = pattern.lower()
        self.pattern = pattern

        try:
            self.parser = createParser(self.filename)
        except InputStreamError as err:
            error("Unable to open file: %s" % err)
            sys.exit(1)
        if not self.parser:
            error("Unable to parse file: %s" % self.filename)
            sys.exit(1)

        with self.parser:
            try:
                self.grep(self.parser)
            except IOError as err:
                if err[0] == errno.EPIPE:
                    # Ignore broken PIPE error
                    return
                else:
                    raise


def runGrep(values, pattern, filenames):
    grep = ConsoleGrep()
    grep.display_filename = (1 < len(filenames))
    grep.display_address = not(values.no_addr)
    grep.display_path = values.path
    grep.display_value = not(values.no_value)
    grep.display_percent = values.percent
    grep.display = not(values.bench)
    for filename in filenames:
        grep.searchFile(filename, pattern, case_sensitive=values.case)


def main():
    try:
        values, pattern, filenames = parseOptions()
        configureHachoir(values)
        if values.bench:
            bench = Benchmark()
            bench.run(runGrep, values, pattern, filenames)
        else:
            runGrep(values, pattern, filenames)
    except KeyboardInterrupt:
        print("Program interrupted (CTRL+C).")
        sys.exit(1)


if __name__ == '__main__':
    main()
