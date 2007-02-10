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
    UInt32, UInt16, UInt8, Int8, Float32, Enum,
    RawBytes, String, GenericVector, ParserError)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN
from hachoir_core.text_handler import humanFilesize, hexadecimal

def parseSigned(val):
    return "%i" % (val.value-128)

MAX_ENVPOINTS = 32
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
    
class Instrument(FieldSet):
    def createFields(self):
        yield UInt32(self, "size", text_handler=humanFilesize)
        yield String(self, "name", 22, charset="ASCII", strip=" \0")
        yield UInt8(self, "type")
        yield UInt16(self, "samples")
        num = self["samples"].value
        self.info("Instrument '%s' has %i samples" % (self["name"].display, self["samples"].value))
        # ValueError: generator already executing
        if num == 1:
            yield InstrumentSecondHeader(self, "second_header")
            yield SampleHeader(self, "sample_header")
            size = self["sample_header/length"].value
            if size > 0:
                yield RawBytes(self, "sample_data", size, r"Deltas")
        if num > 1:
            yield InstrumentSecondHeader(self, "second_header")

            for idx in xrange(num):
                yield SampleHeader(self, "sample_header[]")
                
            for header in self.array("sample_header"):
                size = header["length"].value
                if size > 0:
                    yield RawBytes(self, "sample_data[]", size, "Deltas")

    def createDescription(self):
        return "%s, %u samples" % (self["name"].display, self["samples"].value)

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

class Pattern(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self._size = 8*(self["data_size"].value + 9)

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

def parseComments(s):
    size = s["block_size"].value
    if size > 0:
        yield String(s, "comment", size)

class MidiOut(FieldSet):
    static_size = 9*32*8
    def createFields(self):
        for name in ("start", "stop", "tick", "noteon", "noteoff",
                     "volume", "pan", "banksel", "program"):
            yield String(self, name, 32, strip='\0')

class Command(FieldSet):
    static_size = 32*8
    def createFields(self):
        start = self.absolute_address
        size = self.stream.searchBytesLength("\0", False, start)
        if size > 0:
            self.info("Command: %s" % self.stream.readBytes(start, size))
            yield String(self, "command", size, strip='\0')
        yield RawBytes(self, "parameter", (self._size//8)-size)

class MidiSFXExt(FieldSet):
    static_size = 16*32*8
    def createFields(self):
        for idx in xrange(16):
            yield Command(self, "command[]")

class MidiZXXExt(FieldSet):
    static_size = 128*32*8
    def createFields(self):
        for idx in xrange(128):
            yield Command(self, "command[]")

def parseMidiConfig(s):
    yield MidiOut(s, "midi_out")
    yield MidiSFXExt(s, "sfx_ext")
    yield MidiZXXExt(s, "zxx_ext")

def parseChannelSettings(s):
    size = s["block_size"].value//4
    if size > 0:
        yield GenericVector(s, "settings", size, UInt32, "mix_plugin")

def parseEQBands(s):
    size = s["block_size"].value//4
    if size > 0:
        yield GenericVector(s, "gains", size, UInt32, "band")

class SoundMixPluginInfo(FieldSet):
    static_size = (4+4+4+4+16+32+64)*8
    def createFields(self):
        yield UInt32(self, "plugin_id1", text_handler=hexadecimal)
        yield UInt32(self, "plugin_id2", text_handler=hexadecimal)
        yield UInt32(self, "input_routing")
        yield UInt32(self, "output_routing")
        yield GenericVector(self, "routing_info", 4, UInt32, "reserved")
        yield String(self, "name", 32, strip='\0')
        yield String(self, "dll_name", 64, desc="Original DLL name", strip='\0')

class ExtraData(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self._size = (4+self["size"])*8
    def createFields(self):
        yield UInt32(self, "size")
        size = self["size"].value
        if size > 0:
            yield RawBytes(self, "data", size)

class XPlugData(FieldSet):
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self._size = (4+self["size"])*8
    def createFields(self):
        yield UInt32(self, "size")
        while not self.eof:
            yield UInt32(self, "marker")
            if self["marker"].value == 'DWRT':
                yield Float32(self, "dry_ratio")
            elif self["marker"].value == 'PORG':
                yield UInt32(self, "default_program")
        
def parsePlugin(s):
    yield SoundMixPluginInfo(s, "info")

    # Check if VST setchunk present
    size = s.stream.readBits(s.absolute_address+s.current_size, 32, LITTLE_ENDIAN)
    if size > 0 and size < s.current_size + s._size:
        yield ExtraData(s, "extra_data")

    # Check if XPlugData is present
    size = s.stream.readBits(s.absolute_address+s.current_size, 32, LITTLE_ENDIAN)
    if size > 0 and size < s.current_size + s._size:
        yield XPlugData(s, "xplug_data")

# Format: "XXXX": (type, count, name)
EXTENSIONS = {
    # WriteInstrumentHeaderStruct@Sndfile.cpp
    "XTPM": {
         "..Fd": (UInt32, 1, "Flags"),
         "..OF": (UInt32, 1, "Fade out"),
         "..VG": (UInt32, 1, "Global Volume"),
         "...P": (UInt32, 1, "Paning"),
         "..EV": (UInt32, 1, "Volument Enveloppe"),
         "..EP": (UInt32, 1, "Panning Envelopped"),
         ".EiP": (UInt32, 1, "Pitch envelopped"),
         ".SLV": (UInt8, 1, "Volume Loop Start"),
         ".ELV": (UInt8, 1, "Volume Loop End"),
         ".BSV": (UInt8, 1, "Volume Sustain Begin"),
         ".ESV": (UInt8, 1, "Volume Sustain End"),
         ".SLP": (UInt8, 1, "Panning Loop Start"),
         ".ELP": (UInt8, 1, "Panning Loop End"),
         ".BSP": (UInt8, 1, "Panning Substain Begin"),
         ".ESP": (UInt8, 1, "Padding Substain End"),
         "SLiP": (UInt8, 1, "Pitch Loop Start"),
         "ELiP": (UInt8, 1, "Pitch Loop End"),
         "BSiP": (UInt8, 1, "Pitch Substain Begin"),
         "ESiP": (UInt8, 1, "Pitch Substain End"),
         ".ANN": (UInt8, 1, "NNA"),
         ".TCD": (UInt8, 1, "DCT"),
         ".AND": (UInt8, 1, "DNA"),
         "..SP": (UInt8, 1, "Pannning Swing"),
         "..SV": (UInt8, 1, "Volume Swing"),
         ".CFI": (UInt8, 1, "IFC"),
         ".RFI": (UInt8, 1, "IFR"),
         "..BM": (UInt32, 1, "Midi Bank"),
         "..PM": (UInt8, 1, "Midi Program"),
         "..CM": (UInt8, 1, "Midi Channel"),
         ".KDM": (UInt8, 1, "Midi Drum Key"),
         ".SPP": (Int8, 1, "PPS"),
         ".CPP": (UInt8, 1, "PPC"),
         ".[PV": (UInt32, MAX_ENVPOINTS, "Volume Points"),
         ".[PP": (UInt32, MAX_ENVPOINTS, "Panning Points"),
         "[PiP": (UInt32, MAX_ENVPOINTS, "Pitch Points"),
         ".[EV": (UInt8, MAX_ENVPOINTS, "Volume Enveloppe"),
         ".[EP": (UInt8, MAX_ENVPOINTS, "Panning Enveloppe"),
         "[EiP": (UInt8, MAX_ENVPOINTS, "Pitch Enveloppe"),
         ".[MN": (UInt8, 128, "Note Mapping"),
         "..[K": (UInt32, 128, "Keyboard"),
         "..[n": (String, 32, "Name"),
         ".[nf": (String, 12, "Filename"),
         ".PiM": (UInt8, 1, "MixPlug"),
         "..RV": (UInt16, 1, "Volume ramping"),
         "...R": (UInt16, 1, "Resampling"),
         "..SC": (UInt8, 1, "Cut Swing"),
         "..SR": (UInt8, 1, "Res Swing"),
         "..MF": (UInt8, 1, "Filter Mode"),
    },

    # See after "CODE tag dictionnary", same place, elements with [EXT]
    "STPM": {
         "...C": (UInt32, 1, "Channels"),
         ".VWC": (None, 0, "CreatedWith version"),
         ".VGD": (None, 0, "Default global volume"),
         "..TD": (None, 0, "Default tempo"),
         "HIBE": (None, 0, "Embedded instrument header"),
         "VWSL": (None, 0, "LastSavedWith version"),
         ".MMP": (None, 0, "Plugin Mix mode"),
         ".BPR": (None, 0, "Rows per beat"),
         ".MPR": (None, 0, "Rows per measure"),
         "@PES": (None, 0, "Chunk separaror"),
         ".APS": (None, 0, "Song Pre-amplification"),
         "..MT": (None, 0, "Tempo mode"),
         "VTSV": (None, 0, "VSTi volume"),
    }
}

class MPField(FieldSet):
    def __init__(self, parent, name, ext, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self.ext = ext
        self.info(self.createDescription())
        self._size = (6+self["data_size"].value)*8

    def createFields(self):
        # Identify tag
        code = self.stream.readBytes(self.absolute_address, 4)
        Type, Count, Comment = RawBytes, 1, "Unknown tag"
        if code in self.ext:
            Type, Count, Comment = self.ext[code]

        # Header
        yield String(self, "code", 4, Comment)
        yield UInt16(self, "data_size")

        # Data
        if Type == None:
            size = self["data_size"].value
            if size > 0:
                yield RawBytes(self, "data", size)
        elif Type == String or Type == RawBytes:
            yield Type(self, "value", Count)
        else:
            if Count > 1:
                yield GenericVector(self, "values", Count, Type, "item")
            else:
                yield Type(self, "value")

    def createDescription(self):
        return "Element '%s', size %i" % \
               (self["code"]._description, self["data_size"].value)

def parseFields(s):
    # Determine field names
    ext = EXTENSIONS[s["block_type"].value]
    if ext == None:
        raise ParserError("Unknown parent '%s'" % s["block_type"].value)

    # Parse fields
    addr = s.absolute_address + s.current_size
    while not s.eof and s.stream.readBytes(addr, 4) in ext:
        field = MPField(s, "field[]", ext)
        yield field
        addr += field._size

    # Abort on unknown codes, 
    s.info("End of extension '%s' when finding '%s'" %
           (s["block_type"].value, s.stream.readBytes(addr, 4)))

class Block(FieldSet):
    BLOCK_INFO = {
        "TEXT": ("comment", True, "Comment", parseComments),
        "MIDI": ("midi_config", True, "Midi configuration", parseMidiConfig),
        "XFHC": ("channel_settings", True, "Channel settings", parseChannelSettings),
        "XTPM": ("instrument_ext", False, "Instruement extensions", parseFields),
        "STPM": ("song_ext", False, "Song extensions", parseFields),
    }
    def __init__(self, parent, name, desc=None):
        FieldSet.__init__(self, parent, name, desc)
        self.parseBlock = parsePlugin
        
        t = self["block_type"].value
        self.has_size = False
        if t in self.BLOCK_INFO:
            self._name, self.has_size, desc, parseBlock = self.BLOCK_INFO[t]
            if callable(desc):
                self.createDescription = lambda: desc(self)
            if parseBlock:
                self.parseBlock = lambda: parseBlock(self)

        if self.has_size:
            self._size = 8*(self["block_size"].value + 8)
            
    def createFields(self):
        yield String(self, "block_type", 4)
        if self.has_size:
            yield UInt32(self, "block_size")

        if self.parseBlock:
            for field in self.parseBlock():
                yield field

        if self.has_size:
            size = self["block_size"].value - (self.current_size//8)
            if size > 0:
                yield RawBytes(self, "data", size, "Unknow data")

class XMFile(Parser):
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

        # Undocumented part found in ModPlug
        while not self.eof:
            block = Block(self, "block[]")
            yield block
            if block["block_type"].value == "STPM":
                break

        # More undocumented stuff: date ?
        size = (self._size - self.absolute_address - self.current_size)//8
        if size > 0:
            yield String(self, "info", size, strip='\0\n')

    def createDescription(self):
        return self["header"].createDescription()
