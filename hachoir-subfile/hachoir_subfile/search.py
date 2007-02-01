from hachoir_core.cmd_line import unicodeFilename
from hachoir_core.error import HACHOIR_ERRORS, error
from hachoir_core.stream import FileInputStream, InputSubStream
from hachoir_core.tools import humanFilesize, humanDuration, makePrintable
from hachoir_parser import QueryParser
from hachoir_subfile.create_regex import createRegex
from hachoir_subfile.memory import getTotalMemory, setMemoryLimit
from hachoir_subfile.data_rate import DataRate
from hachoir_subfile.output import Output
from sys import stderr
from time import time
import re

def skipSubfile(parser):
    return ("subfile" in parser.tags) and (parser.tags["subfile"] == "skip")

FILE_MAX_SIZE = 100 * 1024 * 1024   # Max. file size in bytes (100 MB)
SLICE_SIZE = 64*1024                # Slice size in bytes (64 KB)
HARD_MEMORY_LIMIT = 100*1024*1024
PROGRESS_UPDATE = 1.5   # Minimum number of second between two progress messages


def inputStreamSearchRegex(stream, regex, start, end):
    data = stream.readBytes(start, (end-start)//8)
    return [ (match.group(0), start+match.start(0)*8)
        for match in regex.finditer(data) ]

class SearchSubfile:
    """
    Tool to find file start and file size in any binary stream.

    To use it:
    - instanciate the class: subfile = SearchSubfile()
    - (optional) choose magics with: subfile.loadMagics(categories, parser_ids)
    - run the search: subfile.main()
    """
    def __init__(self, filename, directory, offset=0, size=None, verbose=True, debug=True):
        """
        Setup search tool, parameter:
         - filename: Input filename in locale charset
         - directory: Directory filename in locale charset where
           output files will be written
         - offset: Offset (in bytes) of the beginning of the search
         - size: Limit size (in bytes) of input file (None: no limit)
         - debug: Debug mode flag (display debug information)
        """
        self.verbose = verbose
        self.debug = debug
        self.stream = FileInputStream(unicodeFilename(filename), real_filename=filename)
        if size is not None:
            self.size = min(self.stream.size, (offset+size)*8)
        else:
            self.size = self.stream.size
        self.slice_size = SLICE_SIZE*8   # 64 KB (in bits)
        self.start_offset = offset*8
        self.datarate = DataRate(self.start_offset)
        if directory:
            self.output = Output(directory)
        else:
            self.output = None
        self.total_mem = getTotalMemory()
        self.mem_limit = None
        self.main_start = time()
        self.filter = None
        self.magics = []

    def loadMagics(self, categories=None, parser_ids=None):
        # Choose parsers to use
        tags = []
        if categories: tags += [ ("category", cat) for cat in categories ]
        if parser_ids: tags += [ ("id", parser_id) for parser_id in parser_ids ]
        if tags      : tags += [ None ]
        parser_list = QueryParser(tags)

        # Load parser magics
        magics = []
        for parser in parser_list:
            for (magic, offset) in parser.getTags().get("magic",()):
                if self.slice_size < offset:
                    self.slice_size = offset + 8
                    error("Use slice size of %s because of '%s' parser magic offset" % (
                        (self.slice_size//8), parser.__name__))
                magics.append((magic, offset, parser))

        # Build regex
        self.max_magic_len = max( len(magic) for magic in magics )
        self.magics = {}
        magic_strings = []
        for magic, offset, parser in magics:
            magic_strings.append(magic)
            self.magics[magic] = (offset, parser)
        regex = createRegex(magic_strings)
        if self.debug:
            print "Use regex >>>%s<<<" % makePrintable(regex, "ASCII")
        self.magic_regex = re.compile(regex)

    def main(self):
        """
        Run the search.
        Return True if ok, False otherwise.
        """

        # Initialize
        if not self.magics:
            self.loadMagics()
        self.limitMemory()
        self.mainHeader()

        # Prepare search
        main_error = False
        try:
            # Run search
            self.searchSubfiles()
        except KeyboardInterrupt:
            print >>stderr, "[!] Program interrupted (CTRL+C)"
            main_error = True
        except MemoryError:
            main_error = True
            if not self.total_mem:
                raise
            setMemoryLimit(self.total_mem)   # Disable memory limit
            print >>stderr, "[!] Memory error: %s limit exceed!" % humanFilesize(self.mem_limit)
        self.mainFooter()
        return not(main_error)

    def mainHeader(self):
        print >>stderr, "[+] Start search (%s)" % \
            humanFilesize((self.size-self.start_offset)//8)
        print >>stderr
        self.stats = {}
        self.current_offset = self.start_offset
        self.main_start = time()

    def limitMemory(self):
        if not self.total_mem:
            return
        self.mem_limit = min(int(0.25 * self.total_mem), HARD_MEMORY_LIMIT)
        if setMemoryLimit(self.mem_limit):
            print >>stderr, "Set maximum memory to %s" % humanFilesize(self.mem_limit)
        else:
            print >>stderr, "(unable to set memory limit)"

    def mainFooter(self):
        print >>stderr
        print >>stderr, "[+] End of search -- offset=%s (%s)" % (
            self.current_offset//8, humanFilesize(self.current_offset//8))
        size = (self.current_offset - self.start_offset) // 8
        duration = time() - self.main_start
        if 0.1 <= duration:
            print >>stderr, "Total time: %s -- global rate: %s/sec" % (
                humanDuration(duration*1000), humanFilesize(size // duration))

    def searchSubfiles(self):
        """
        Search all subfiles in the stream, call processParser() for each parser.
        """
        self.next_offset = None
        self.next_progress = time() + PROGRESS_UPDATE
        while self.current_offset < self.size:
            self.datarate.update(self.current_offset)
            if self.verbose and self.next_progress <= time():
                self.displayProgress()
            found = []
            for parser in self.findMagic(self.current_offset):
                found.append(parser)
            for offset, parser in sorted(found):
                self.processParser(offset, parser)
            self.current_offset += self.slice_size
            if self.next_offset:
                self.current_offset = max(self.current_offset, self.next_offset)

    def processParser(self, offset, parser):
        """
        Process a valid parser.
        """
        format = parser.__class__.__name__
        if self.debug:
            print >>stderr, "Found %s at offset %s" % (format, offset//8)
        text = "[+] Found file at %s" % (offset//8)
        if parser.content_size is not None:
            text += " size=%s (%s)" % (parser.content_size//8, humanFilesize(parser.content_size//8))
        if not(parser.content_size) or parser.content_size//8 < FILE_MAX_SIZE:
            text += ": " + parser.description
        else:
            text += ": " + format

        if self.output and parser.content_size:
            if (offset == 0 and parser.content_size == self.size):
                text += " (don't copy whole file)"
            elif parser.content_size//8 >= FILE_MAX_SIZE:
                text += " (don't copy file, too big)"
            elif not self.filter or self.filter(parser):
                filename = self.output.createFilename(parser.filename_suffix)
                filename = self.output.writeFile(filename, self.stream, offset, parser.content_size)
                text += " => %s" % filename
        print text
        self.next_progress = time() + PROGRESS_UPDATE

    def findMagic(self, offset):
        """
        Find all 'magic_str' strings in stream in offset interval:
          offset..(offset+self.slice_size).

        The function returns a generator with values (offset, parser) where
        offset is beginning of a file (relative to stream begin), and not the
        position of the magic.
        """
        max_offset = offset + self.slice_size + 8 * (self.max_magic_len-1)
        max_offset = min(max_offset, self.size)
        for magic, offset in inputStreamSearchRegex(self.stream, self.magic_regex, offset, max_offset):
            # Compute file offset start
            magic_offset, parser_cls = self.magics[magic]
            offset -= magic_offset

            # Skip invalid offset
            if offset < 0:
                continue
            if offset < self.next_offset:
                continue

            # Create parser at found offset
            parser = self.guess(offset, parser_cls)

            # Update statistics
            if parser_cls not in self.stats:
                self.stats[parser_cls] = [0, 0]
            self.stats[parser_cls][0] += 1
            if not parser:
                continue

            # Parser is valid, yield it with the offset
            self.stats[parser_cls][1] += 1
            yield (offset, parser)

            # Set next offset
            if parser.content_size is not None\
            and skipSubfile(parser):
                self.next_offset = offset + parser.content_size
                if max_offset < self.next_offset:
                    break

    def guess(self, offset, parser_cls):
        """
        Try the specified parser at stream offset 'offset'.

        Return the parser object, or None on failure.
        """
        substream = InputSubStream(self.stream, offset)
        try:
            return parser_cls(substream, validate=True)
        except HACHOIR_ERRORS:
            return None

    def displayProgress(self):
        """
        Display progress (to stdout) of the whole process.
        Compute data rate (in byte per sec) and time estimation.
        """
        # Program next update
        self.next_progress = time() + PROGRESS_UPDATE

        # Progress offset
        percent = float(self.current_offset - self.start_offset) * 100 / (self.size - self.start_offset)
        offset = self.current_offset // 8
        message = "Search: %.2f%% -- offset=%u (%s)" % (
            percent, offset, humanFilesize(offset))

        # Compute data rate (byte/sec)
        average = self.datarate.average
        if average:
            message += " -- %s/sec " % humanFilesize(average // 8)
            eta = float(self.size - self.current_offset) / average
            message += " -- ETA: %s" % humanDuration(eta * 1000)

        # Display message
        print >>stderr, message

