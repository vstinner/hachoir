"""
The ScreamTracker 3.0x module format description for .s3m files.

Documents:
- Search s3m on Wotsit
  http://www.wotsit.org/

Author: Christophe GISQUET <christophe.gisquet@free.fr>
Creation: 11th February 2007
"""

from hachoir_parser import Parser
from hachoir_core.field import (StaticFieldSet, FieldSet, Field,
    Bit, Bits,
    UInt32, UInt16, UInt8, Enum,
    RawBytes, String, GenericVector)
from hachoir_core.endian import LITTLE_ENDIAN
from hachoir_core.text_handler import hexadecimal, humanFrequency
from hachoir_core.tools import alignValue

class Chunk:
    def __init__(self, cls, offset, size, *args):
        assert size != None
        self.cls = cls
        self.offset = offset
        self.size = size
        self.args = args

class ChunkIndexer:
    def __init__(self):
        self.chunks = [ ]

    # Newest element is last
    def addChunk(self, new_chunk):
        if len(self.chunks) > 0:
            # Find first chunk whose value is bigger
            index = 0
            while index < len(self.chunks):
                offset = self.chunks[index].offset
                if offset < new_chunk.offset:
##                    print "Added element %u: size=%u position=%u>%u" % \
##                          (index, new_chunk.size, new_chunk.offset, offset)
                    self.chunks.insert(index, new_chunk)
                    return
                index += 1

        # Not found or empty
##        print "Appended element %u of size %u at position %u" % \
##              (len(self.chunks)+1, new_chunk.size, new_chunk.offset)
        self.chunks.append(new_chunk)

    def yieldChunks(self, obj):
        while len(self.chunks) > 0:
            chunk = self.chunks.pop()
            current_pos = obj.current_size//8

            # Check if padding needed
            size = chunk.offset - current_pos
            if size > 0:
                obj.info("Padding of %u bytes needed: curr=%u offset=%u" % \
                         (size, current_pos, chunk.offset))
                yield RawBytes(obj, "padding[]", size)
                current_pos = obj.current_size//8

            # Find resynch point if needed
            count = 0
            old_off = chunk.offset
            while chunk.offset < current_pos:
                count += 1
                chunk = self.chunks.pop()
                # Unfortunaly, we also pass the underlying chunks
                if chunk == None:
                    obj.info("Couldn't resynch: %u object skipped to reach %u" % \
                             (count, current_pos))
                    return

            # Resynch
            size = chunk.offset-current_pos
            if size > 0:
                obj.info("Skipped %u objects to resynch to %u; chunk offset: %u->%u" % \
                         (count, current_pos, old_off, chunk.offset))
                yield RawBytes(obj, "resynch[]", size)

            # Yield
            obj.info("Yielding element of size %u at offset %u" % \
                     (chunk.size, chunk.offset))
            field = chunk.cls(obj, *chunk.args)
            # Not tested, probably wrong:
            #if chunk.size: field.static_size = 8*chunk.size
            yield field

            if hasattr(field, "getSubChunk"):
                sub_chunk = field.getSubChunk()
                obj.info("Adding a sub chunk with position %u" % sub_chunk.offset)
                self.addChunk(sub_chunk)

            # Compare sizes expected and produced for further padding,
            # but check it against object size, if known
            size = chunk.size - (field._size//8)
            if obj._size != None and \
                   obj.absolute_address + obj.current_size + 8*size > obj._size:
                size = (obj._size-obj.absolute_address-obj.current_size)//8

            # Padd as required
            if size > 0:
                obj.info("Warning: chunk too small, %u padding bytes added" % size)
                yield RawBytes(obj, "padding[]", size)
            elif size < 0 and chunk.size > 0:
                obj.info("Warning: chunk too big: %u additional bytes" % -size)


class Flags(StaticFieldSet):
    format = (
        (Bit, "st2_vibrato", "Vibrato (File version 1/ScreamTrack 2)"),
        (Bit, "st2_tempo", "Tempo (File version 1/ScreamTrack 2)"),
        (Bit, "amiga_slides", "Amiga slides (File version 1/ScreamTrack 2)"),
        (Bit, "zero_vol_opt", "Automatically turn off looping notes whose volume is zero for >2 note rows"),
        (Bit, "amiga_limits", "Disallow notes beyong Amiga hardware specs"),
        (Bit, "sb_processing", "Enable filter/SFX with SoundBlaster"),
        (Bit, "vol_slide", "Volume slide also performed on first row"),
        (Bit, "extended", "Special custom data in file"),
        (Bits, "unused[]", 8)
    )

def parseChannelType(val):
    val = val.value
    if val<8:
        return "Left Sample Channel %u" % val
    if val<16:
        return "Right Sample Channel %u" % (val-8)
    if val<32:
        return "Adlib channel %u" % (val-16)
    return "Value %u unhandled" % val

class ChannelSettings(FieldSet):
    static_size = 8
    def createFields(self):
        yield Bits(self, "type", 7, text_handler=parseChannelType)
        yield Bit(self, "enabled")

class ChannelPanning(FieldSet):
    static_size = 8
    def createFields(self):
        yield Bits(self, "default_position", 4, "Default pan position")
        yield Bit(self, "reserved[]")
        yield Bit(self, "use_default", "Bits 0:3 specify default position")
        yield Bits(self, "reserved[]", 2)

SCREAMTRACKER_VERSION = {
    0x1300: "ScreamTracker 3.00",
    0x1301: "ScreamTracker 3.01",
    0x1303: "ScreamTracker 3.03",
    0x1320: "ScreamTracker 3.20"
}

class Header(FieldSet):
    """
          0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0000: | Song name, max 28 chars (end with NUL (0))                    |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0010: |                                               |1Ah|Typ| x | x |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0020: |OrdNum |InsNum |PatNum | Flags | Cwt/v | Ffi   |'S'|'C'|'R'|'M'|
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0030: |g.v|i.s|i.t|m.v|u.c|d.p| x | x | x | x | x | x | x | x |Special|
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0040: |Channel settings for 32 channels, 255=unused,+128=disabled     |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0050: |                                                               |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0060: |Orders; length=OrdNum (should be even)                         |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  xxx1: |Parapointers to instruments; length=InsNum*2                   |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  xxx2: |Parapointers to patterns; length=PatNum*2                      |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  xxx3: |Channel default pan positions                                  |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
        xxx1=70h+orders
        xxx2=70h+orders+instruments*2
        xxx3=70h+orders+instruments*2+patterns*2
    """
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        start = self.absolute_address
        ordnum = self.stream.readBits(start+0x20*8, 16, LITTLE_ENDIAN)
        insnum = self.stream.readBits(start+0x22*8, 16, LITTLE_ENDIAN)
        patnum = self.stream.readBits(start+0x24*8, 16, LITTLE_ENDIAN)
        size = 0x60+ordnum+2*insnum+2*patnum
        if self.stream.readBits(start+0x35*8, 8, LITTLE_ENDIAN) == 252:
            size += 32
        self._size = alignValue(size, 16) * 8

    def createDescription(self):
        return "%s (%u patterns, %u instruments)" % \
               (self["title"].value, self["num_patterns"].value,
                self["num_instruments"].value)

    def createValue(self):
        return self["title"].value

    def createFields(self):
        yield String(self, "title", 28, strip='\0')
        yield UInt8(self, "marker[]", text_handler=hexadecimal)
        yield UInt8(self, "type")
        yield RawBytes(self, "reserved[]", 2)

        yield UInt16(self, "num_orders")
        yield UInt16(self, "num_instruments")
        yield UInt16(self, "num_patterns")

        yield Flags(self, "flags")
        yield Enum(UInt16(self, "creation_version"), SCREAMTRACKER_VERSION)
        yield UInt16(self, "format_version")
        yield String(self, "marker[]", 4, "Is SCRM")

        yield UInt8(self, "glob_vol", "Global volume")
        yield UInt8(self, "init_speed", "Initial speed (command A)")
        yield UInt8(self, "init_tempo", "Initial tempo (command T)")
        yield Bits(self, "volume", 7)
        yield Bit(self, "stereo")
        yield UInt8(self, "click_removal", "Number of GUS channels to run to prevent clicks")
        yield UInt8(self, "panning_info")
        yield RawBytes(self, "reserved[]", 8)
        yield UInt16(self, "custom_data_parapointer",
                     "Parapointer to special custom data (not used by ST3.01)")

        yield GenericVector(self, "channel_settings", 32, ChannelSettings, "channel")

        # Orders
        orders = self["num_orders"].value
        instr = self["num_instruments"].value
        patterns = self["num_patterns"].value
        self.info("Header: orders=%u instruments=%u patterns=%u" %
                  (orders, instr, patterns))
        if orders == 0:
            orders = 2
        yield GenericVector(self, "orders", orders, UInt8, "order")
        if orders&1:
            yield RawBytes(self, "padding", 1)

        # File pointers
        if instr > 0:
            yield GenericVector(self, "instr_pptr", instr, UInt16, "offset")
        if patterns > 0:
            yield GenericVector(self, "pattern_pptr", patterns, UInt16, "offset")

        # S3M 3.20 extension
        if self["creation_version"].value >= 0x1320 and \
               self["panning_info"].value == 252:
            yield GenericVector(self, "channel_panning", 32, ChannelPanning, "channel")

        # Padding required for 16B alignment
        size = self._size - self.current_size
        if size > 0:
            yield RawBytes(self, "padding", size//8)

class OldInstrument(FieldSet):
    """
    Probably used in older ST3 version. Description follows:

          0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0000: |[T]| Dos filename (12345678.123)                   |00h|00h|00h|
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0010: |D00|D01|D02|D0||D04|D05|D06|D07|D08|D09|D0A|D0B|Vol|Dsk| x | x |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0020: |C2Spd  |HI:C2sp| x | x | x | x | x | x | x | x | x | x | x | x |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0030: | Sample name, 28 characters max... (incl. NUL)                 |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0040: | ...sample name...                             |'S'|'C'|'R'|'I'|
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    """

    TYPES = {2:"amel", 3:"abd", 4:"asnare", 5:"atom", 6:"acym", 7:"ahihat" }
    MAGIC = "SCRI"
    static_size = 0x50*8

    def createFields(self):
        yield Enum(UInt8(self, "type"), self.TYPES)
        yield String(self, "filename", 12, strip='\0')
        yield RawBytes(self, "reserved[]", 3)
        yield RawBytes(self, "adlib_specs", 12)
        yield UInt8(self, "volume")
        yield UInt8(self, "disk")
        yield RawBytes(self, "reserved[]", 2)
        yield UInt32(self, "c2_speed", "Frequency for middle C note", text_handler=humanFrequency)
        yield RawBytes(self, "reserved[]", 12)
        yield String(self, "name", 28, strip='\0')
        yield String(self, "marker", 4, "Either 'SCRI' or '(empty)'", strip='\0')

class SampleFlags(StaticFieldSet):
    format = (
        (Bit, "loop_on"),
        (Bit, "stereo", "Sample size will be 2*length"),
        (Bit, "16bits", "16b sample, Intel LO-HI byteorder"),
        (Bits, "unused", 5)
    )

class S3MUInt24(Field):
    static_size = 24
    def __init__(self, parent, name, desc=None):
        Field.__init__(self, parent, name, size=24, description=desc)
        addr = self.absolute_address
        val = parent.stream.readBits(addr, 8, LITTLE_ENDIAN) << 20
        val += parent.stream.readBits(addr+8, 16, LITTLE_ENDIAN) << 4
        self.createValue = lambda: val

class SampleData(FieldSet):
    def __init__(self, parent, name, padded_size, real_size, desc=None):
        FieldSet.__init__(self, parent, name, description=desc)
        padded_size *= 8
        if self.absolute_address + padded_size > self._parent._size:
            self._size = self._parent._size-self.absolute_address
        else:
            self._size = padded_size
        self.real_size = real_size

    def createFields(self):
        yield RawBytes(self, "data", self.real_size)
        size = (self._size - self.current_size)//8
        if size > 0:
            yield RawBytes(self, "padding", size)

class NewInstrument(FieldSet):
    """
    In fact a sample. Description follows:

          0   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0000: |[T]| Dos filename (12345678.ABC)                   |    MemSeg |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0010: |Length |HI:leng|LoopBeg|HI:LBeg|LoopEnd|HI:Lend|Vol| x |[P]|[F]|
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0020: |C2Spd  |HI:C2sp| x | x | x | x |Int:Gp |Int:512|Int:lastused   |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0030: | Sample name, 28 characters max... (incl. NUL)                 |
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  0040: | ...sample name...                             |'S'|'C'|'R'|'S'|
        +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
  xxxx: sampledata
    """

    static_size = 8*0x50
    MAGIC = "SCRS"
    TYPES = {1: "Sample", 2: "adlib melody", 3: "adlib drum2" }
    PACKING = {0: "Unpacked", 1: "DP30ADPCM" }

    def createFields(self):
        yield Enum(UInt8(self, "type"), self.TYPES)
        yield String(self, "filename", 12, strip='\0')
        yield S3MUInt24(self, "data_position")
        yield UInt32(self, "data_length")
        yield UInt32(self, "loop_begin")
        yield UInt32(self, "loop_end")
        yield UInt8(self, "volume")
        yield UInt8(self, "reserved[]")
        yield Enum(UInt8(self, "packing"), self.PACKING)
        yield SampleFlags(self, "flags")
        yield UInt32(self, "c2_speed", "Frequency for middle C note", text_handler=humanFrequency)
        yield UInt32(self, "reserved[]", 4)
        yield UInt16(self, "internal[]", "Sample addresss in GUS memory")
        yield UInt16(self, "internal[]", "Flags for SoundBlaster loop expansion")
        yield UInt32(self, "internal[]", "Last used position (SB)")
        yield String(self, "name", 28, strip='\0')
        yield String(self, "marker", 4, "Either 'SCRS' or '(empty)'", strip='\0')

    def getSubChunk(self):
        real_size = self["data_length"].value
        if self["flags/stereo"].value: real_size *= 2
        if self["flags/16bits"].value: real_size *= 2
        padded_size = alignValue(real_size, 16)
        return Chunk(SampleData, self["data_position"].value, padded_size,
                     "sample_data[]", padded_size, real_size)

    def createDescription(self):
        info = "%s, " % self["c2_speed"].display
        size = self["data_length"].value

        if self["flags/stereo"].value:
            info += "stereo, "
            size *= 2
        else:
            info += "mono, "

        if self["flags/16bits"].value:
            return info + "16bits, %uB" % (size*2)
        else:
            return info + "8bits, %uB" % size

    def createValue(self):
        return self["name"].value

class NoteInfo(StaticFieldSet):
    """
0=end of row
&31=channel
&32=follows;  BYTE:note, BYTE:instrument
&64=follows;  BYTE:volume
&128=follows; BYTE:command, BYTE:info
    """
    format = (
        (Bits, "channel", 5),
        (Bit, "has_note"),
        (Bit, "has_volume"),
        (Bit, "has_command")
    )

class Note(FieldSet):
    def createFields(self):
        self.header = self.stream.readBits(self.absolute_address, 8, LITTLE_ENDIAN)
        yield NoteInfo(self, "info")
        if self.header&0x20:
            yield UInt8(self, "note")
            yield UInt8(self, "instrument")
        if self.header&0x40:
            yield UInt8(self, "volume")
        if self.header&0x80:
            yield UInt8(self, "command")
            yield UInt8(self, "param")

class Row(FieldSet):
    def createFields(self):
        while True:
            note = Note(self, "note[]")
            yield note

            # Check empty note
            if note.header == 0:
                break

class Pattern(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)

        # Get size from header
        addr = self.absolute_address
        self.real_size = 8*self.stream.readBits(addr, 16, LITTLE_ENDIAN)

        # But patterns are aligned on 16B<->128b boundaries, it seems
        addr += self.real_size
        addr = alignValue(addr, 128)
        self._size = addr - self.absolute_address
        self.info("Pattern: real=%u aligned=%u" % (self.real_size//8, self._size//8))

    def createFields(self):
        count = 0
        while count < 64 and self.current_size < self.real_size:
            yield Row(self, "row[]")
            count += 1

        size = (self.size - self.current_size) // 8
        if size:
            yield RawBytes(self, "padding", size)

class S3MModule(Parser):
    tags = {
        "id": "s3m",
        "category": "audio",
        "file_ext": ("s3m",),
        "mime": ('audio/s3m', 'audio/x-s3m'),
        "min_size": 64*8,
        "description": "ScreamTracker3 module"
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        marker = self.stream.readBits(0x1C*8, 8, LITTLE_ENDIAN)
        if marker != 0x1A:
            return "Invalid start marker %u" % marker
        marker = self.stream.readBits(0x1D*8, 8, LITTLE_ENDIAN)
        if marker != 16:
            return "Invalid type %u" % marker
        version = self.stream.readBits(0x2A*8, 16, LITTLE_ENDIAN)
        if version not in (1, 2):
            return "Invalid file version %u" % version
        marker = self.stream.readBytes(0x2C*8, 4)
        if marker != "SCRM":
            return "Invalid s3m marker %s" % marker
        return True

    def createFields(self):
        hdr = Header(self, "header")
        yield hdr

        # Index chunks
        indexer = ChunkIndexer()
        for index in xrange(self["header/num_instruments"].value):
            offset = 16*hdr["instr_pptr/offset[%u]" % index].value
            self.info("Adding instrument chunk at offset %u" % offset)
            indexer.addChunk(Chunk(NewInstrument, offset, 0x50, "instrument[]"))

        for index in xrange(self["header/num_patterns"].value):
            offset = 16*hdr["pattern_pptr/offset[%u]" % index].value
            self.info("Adding pattern chunk at offset %u" % offset)
            indexer.addChunk(Chunk(Pattern, offset, 0, "pattern[]"))

        if len(indexer.chunks) > 0:
            for field in indexer.yieldChunks(self):
                yield field

