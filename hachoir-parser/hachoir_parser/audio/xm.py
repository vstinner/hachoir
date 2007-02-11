"""
The XM module format description for XM files version $0104.

Doc:
- http://modplug.svn.sourceforge.net/viewvc/modplug/trunk/modplug/soundlib/Load_xm.cpp?view=markup
- Wotsit.org

Author: Christophe GISQUET <christophe.gisquet@free.fr>
Creation: 8th February 2007
"""

from hachoir_parser import Parser
from hachoir_core.field import (StaticFieldSet, FieldSet,
    Bit, RawBits, Bits,
    UInt32, UInt16, UInt8, Enum,
    RawBytes, String, GenericVector)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN
from hachoir_core.text_handler import humanFilesize, hexadecimal
from hachoir_parser.audio.modplug import ParseModplugMetadata

def parseSigned(val):
    return "%i" % (val.value-128)

SAMPLE_LOOP_MODE = [ "No loop", "Forward loop", "Ping-pong loop", "Undef" ]

class SampleType(FieldSet):
    static_size = 8
    def createFields(self):
        yield Bits(self, "unused[]", 4)
        yield Bit(self, "16bits")
        yield Bits(self, "unused[]", 1)
        yield Enum(Bits(self, "loop_mode", 2), SAMPLE_LOOP_MODE)

class SampleHeader(FieldSet):
    static_size = 40*8
    def createFields(self):
        yield UInt32(self, "length")
        yield UInt32(self, "loop_start")
        yield UInt32(self, "loop_end")
        yield UInt8(self, "volume")
        yield UInt8(self, "fine_tune", text_handler=parseSigned)
        yield SampleType(self, "type")
        yield UInt8(self, "panning")
        yield UInt8(self, "relative_note", text_handler=parseSigned)
        yield UInt8(self, "reserved")
        yield String(self, "name", 22, charset="ASCII", strip=' \0')

    def createDescription(self):
        return "%s, %s" % (self["name"].display, self["type/loop_mode"].display)

class StuffType(StaticFieldSet):
    format = (
        (Bits, "unused", 5),
        (Bit, "loop"),
        (Bit, "sustain"),
        (Bit, "on")
    )

# Unable to get static size of field type: GenericVector
class InstrumentSecondHeader(FieldSet):
    static_size = (263-29)*8
    def createFields(self):
        yield UInt32(self, "sample_header_size")
        yield GenericVector(self, "notes", 96, UInt8, "sample")
        yield GenericVector(self, "volume_envelope", 24, UInt16, "point")
        yield GenericVector(self, "panning_envelope", 24, UInt16, "point")
        yield UInt8(self, "volume_points", r"Number of volume points")
        yield UInt8(self, "panning_points", r"Number of panning points")
        yield UInt8(self, "volume_sustain_point")
        yield UInt8(self, "volume_loop_start_point")
        yield UInt8(self, "volume_loop_end_point")
        yield UInt8(self, "panning_sustain_point")
        yield UInt8(self, "panning_loop_start_point")
        yield UInt8(self, "panning_loop_startwend_point")
        yield StuffType(self, "volume_type")
        yield StuffType(self, "panning_type")
        yield UInt8(self, "vibrato_type")
        yield UInt8(self, "vibrato_sweep")
        yield UInt8(self, "vibrato_depth")
        yield UInt8(self, "vibrato_rate")
        yield UInt16(self, "volume_fadeout")
        yield GenericVector(self, "reserved", 11, UInt16, "word")

def createInstrumentContentSize(s, addr):
    start = addr
    samples = s.stream.readBits(addr+27*8, 16, LITTLE_ENDIAN)
    # Seek to end of header (1st + 2nd part)
    addr += 8*s.stream.readBits(addr, 32, LITTLE_ENDIAN)

    sample_size = 0
    if samples > 0:
        for idx in xrange(samples):
            # Read the sample size from the header
            sample_size += s.stream.readBits(addr, 32, LITTLE_ENDIAN)
            # Seek to next sample header
            addr += SampleHeader.static_size

    return addr - start + 8*sample_size

class Instrument(FieldSet):
    def __init__(self, parent, name):
        FieldSet.__init__(self, parent, name)
        self._size = createInstrumentContentSize(self, self.absolute_address)
        self.info(self.createDescription())

    # Seems to fix things...
    def fixInstrumentHeader(self):
        size = self["size"].value - self.current_size//8
        if size > 0:
            yield RawBytes(self, "unknown_data", size)

    def createFields(self):
        yield UInt32(self, "size")
        yield String(self, "name", 22, charset="ASCII", strip=" \0")
        yield UInt8(self, "type")
        yield UInt16(self, "samples")
        num = self["samples"].value
        self.info(self.createDescription())

        if num > 0:
            yield InstrumentSecondHeader(self, "second_header")

            for field in self.fixInstrumentHeader():
                yield field

            # This part probably wrong
            sample_size = [ ]
            for idx in xrange(num):
                sample = SampleHeader(self, "sample_header[]")
                yield sample
                sample_size.append(sample["length"].value)

            for size in sample_size:
                if size > 0:
                    yield RawBytes(self, "sample_data[]", size, "Deltas")
        else:
            for field in self.fixInstrumentHeader():
                yield field

    def createDescription(self):
        return "Instrument '%s': %i samples, header %i bytes" % \
               (self["name"].display, self["samples"].value, self["size"].value)

VOLUME_NAME = [ "Volume slide down", "Volume slide up", "Fine volume slide down",
                "Fine volume slide up", "Set vibrato speed", "Vibrato",
                "Set panning", "Panning slide left", "Panning slide right",
                "Tone porta", "Unhandled" ]

def parseVolume(val):
    val = val.value
    if 0x10<=val<=0x50:
        return "Volume %i" % val-16
    else:
        return VOLUME_NAME[val/16 - 6]

# Taken from midi.py from V. STINNER
NOTE_NAME = {}
NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "G#", "A", "A#", "B")
for octave in xrange(10):
    for it, note in enumerate(NOTES):
        NOTE_NAME[octave*12+it] = "%s (octave %s)" % (note, octave)

class RealBit(RawBits):
    static_size = 1

    def __init__(self, parent, name, description=None):
        RawBits.__init__(self, parent, name, 1, description=description)

    def createValue(self):
        return self._parent.stream.readBits(self.absolute_address, 1, BIG_ENDIAN)

class NoteInfo(StaticFieldSet):
    format = (
        (RawBits, "unused", 2),
        (RealBit, "has_parameter"),
        (RealBit, "has_type"),
        (RealBit, "has_volume"),
        (RealBit, "has_instrument"),
        (RealBit, "has_note")
    )

EFFECT_NAME = [ "Appregio", "Porta up", "Porta down", "Tone porta", "Vibrato",
                "Tone porta+Volume slide", "Vibrato+Volume slide", "Tremolo",
                "Set panning", "Sample offset", "Volume slide", "Position jump",
                "Set volume", "Pattern break", None, "Set tempo/BPM",
                "Set global volume", "Global volume slide", "Unused", "Unused",
                "Unused", "Set envelope position", "Unused""Unused",
                "Panning slide", "Unused", "Multi retrig note", "Unused",
                "Tremor", "Unused", "Unused", "Unused", None ]

EFFECT_E_NAME = [ "Unknown", "Fine porta up", "Fine porta down",
                  "Set gliss control", "Set vibrato control", "Set finetune",
                  "Set loop begin/loop", "Set tremolo control", "Retrig note",
                  "Fine volume slide up", "Fine volume slide down", "Note cut",
                  "Note delay", "Pattern delay" ]

class Effect(RawBits):
    def __init__(self, parent, name):
        RawBits.__init__(self, parent, name, 8)

    def createValue(self):
        t = self.parent.stream.readBits(self.absolute_address, 8, LITTLE_ENDIAN)
        param = self.parent.stream.readBits(self.absolute_address+8, 8, LITTLE_ENDIAN)
        if t == 0x0E:
            return EFFECT_E_NAME[param>>4] + " %i" % (param&0x07)
        elif t == 0x21:
            return ("Extra fine porta up", "Extra fine porta down")[param>>4]
        else:
            return EFFECT_NAME[t]

# TODO: optimize bitcounting with a table:
# http://graphics.stanford.edu/~seander/bithacks.html#CountBitsSetTable
class Note(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self.flags = self.stream.readBits(self.absolute_address, 8, LITTLE_ENDIAN)
        if self.flags&0x80:
            self._size = 8
            if self.flags&0x01: self._size += 8
            if self.flags&0x02: self._size += 8
            if self.flags&0x04: self._size += 8
            if self.flags&0x08: self._size += 8
            if self.flags&0x10: self._size += 8
        else:
            self._size = 5*8

    def createFields(self):
        # This stupid shit gets the LSB, not the MSB...
        self.info("Note info: 0x%02X" %
                  self.stream.readBits(self.absolute_address, 8, LITTLE_ENDIAN))
        yield RealBit(self, "is_extended")
        info = None
        if self["is_extended"].value:
            info = NoteInfo(self, "info")
            yield info
            if info["has_note"].value:
                yield Enum(UInt8(self, "note"), NOTE_NAME)
        else:
            yield Enum(Bits(self, "note", 7), NOTE_NAME)

        if not info or info["has_instrument"].value:
            yield UInt8(self, "instrument")
        if not info or info["has_volume"].value:
            yield UInt8(self, "volume", text_handler=parseVolume)
        if not info or info["has_type"].value:
            #yield UInt8(self, "effect_type")
            yield Effect(self, "effect_type")
        if not info or info["has_parameter"].value:
            yield UInt8(self, "effect_parameter", text_handler=hexadecimal)

    def createDescription(self):
        desc = []
        info = self["info"]
        if not info or info["has_note"].value:
            desc += self["note"].display
        if not info or info["has_instrument"].value:
            desc += "instrument %i" % self["instrument"].value
        if not info or info["has_volume"].value:
            desc += self["has_volume"].display
        if not info or info["has_type"].value:
            desc += "effect %i" % self["effect_type"].value
        if not info or info["has_parameter"].value:
            desc += "parameter %i" % self["effect_parameter"].value

class Row(FieldSet):
    def createFields(self):
        # Speed-up by removing "/header/channels" look-up ?
        for idx in xrange(self["/header/channels"].value):
            yield Note(self, "note[]")

def createPatternContentSize(s, addr):
    return 8*(s.stream.readBits(addr, 32, LITTLE_ENDIAN) +
              s.stream.readBits(addr+7*8, 16, LITTLE_ENDIAN))

class Pattern(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self._size = createPatternContentSize(self, self.absolute_address)

    def createFields(self):
        yield UInt32(self, "header_size", r"Header length (9)")
        yield UInt8(self, "packing_type", r"Packing type (always 0)")
        yield UInt16(self, "rows", r"Number of rows in pattern (1..256)")
        rows = self["rows"].value
        yield UInt16(self, "data_size", r"Packed patterndata size")
        self.info("Pattern: %i rows" % rows)
        for idx in xrange(rows):
            yield Row(self, "row[]")

    def createDescription(self):
        return "Pattern with %i rows" % self["rows"].value

class Header(FieldSet):
    MAGIC = "Extended Module: "
    static_size = 336*8

    def createFields(self):
        yield String(self, "signature", 17, r"XM signature", charset="ASCII")
        yield String(self, "title", 20, r"XM title", charset="ASCII", strip=' ')
        yield UInt8(self, "marker", r"Marker (0x1A)")
        yield String(self, "tracker_name", 20, r"XM tracker name", charset="ASCII", strip=' ')
        yield UInt8(self, "format_minor")
        yield UInt8(self, "format_major")
        yield UInt32(self, "header_size", r"File header size (0x114)", text_handler=humanFilesize)
        yield UInt16(self, "song_length", r"Length in patten order table")
        yield UInt16(self, "restart", r"Restart position")
        yield UInt16(self, "channels", r"Number of channels (2,4,6,8,10,...,32)")
        yield UInt16(self, "patterns", r"Number of patterns (max 256)")
        yield UInt16(self, "instruments", r"Number of instruments (max 128)")
        yield Bit(self, "amiga_ftable", r"Amiga frequency table")
        yield Bit(self, "linear_ftable", r"Linear frequency table")
        yield Bits(self, "unused", 14)
        yield UInt16(self, "tempo", r"Default tempo")
        yield UInt16(self, "bpm", r"Default BPM")
        yield GenericVector(self, "pattern_order", 256, UInt8, "order")

    def createDescription(self):
        return "'%s' by '%s'" % (
            self["title"].display, self["tracker_name"].value)

class XMModule(Parser):
    tags = {
        "id": "fasttracke2",
        "category": "audio",
        "file_ext": ["xm", ],
        "mime": ('audio/xm', 'audio/x-xm', 'audio/module-xm', 'audio/mod', 'audio/x-mod', ),
        "magic": ((Header.MAGIC, 0),),
        "min_size": (336+29)*8, # Header + 1 empty instrument
        "description": "FastTracker2 module"
    }
    endian = LITTLE_ENDIAN

    def validate(self):
        header = self.stream.readBytes(0, 17)
        if header != Header.MAGIC:
            return "Invalid signature '%s'" % header
        return True

    def createFields(self):
        yield Header(self, "header")
        for idx in xrange(self["/header/patterns"].value):
            yield Pattern(self, "pattern[]")
        for idx in xrange(self["/header/instruments"].value):
            yield Instrument(self, "instrument[]")

        # Metadata added by ModPlug - can be discarded
        for field in ParseModplugMetadata(self):
            yield field

    def createDescription(self):
        return self["header"].createDescription()

    def createContentSize(self):
        start = self.absolute_address
        addr = start
        patterns = self.stream.readBits(addr+70*8, 16, LITTLE_ENDIAN)
        instr = self.stream.readBits(addr+72*8, 16, LITTLE_ENDIAN)
        self.info("XM file has %u patterns and %u instruments" % \
                  (patterns, instr))

        # Get pattern sizes
        addr += Header.static_size
        for idx in xrange(patterns):
            size = createPatternContentSize(self, addr)
            addr += size
            self.info("Pattern %u/%u: %uB" % (idx+1, patterns, size//8))

        # Get instrument sizes
        for idx in xrange(instr):
            size = createInstrumentContentSize(self, addr)
            addr += size
            self.info("Instrument %u/%u: %uB" % (idx+1, instr, size//8))

        return addr-start

