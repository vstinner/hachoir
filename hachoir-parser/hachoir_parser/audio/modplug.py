"""
Modplug metadata inserted into module files.

Doc:
- http://modplug.svn.sourceforge.net/viewvc/modplug/trunk/modplug/soundlib/

Author: Christophe GISQUET <christophe.gisquet@free.fr>
Creation: 10th February 2007
"""

from hachoir_parser import Parser
from hachoir_core.field import (StaticFieldSet, FieldSet,
    Bit, RawBits, Bits,
    UInt32, UInt16, UInt8, Int8, Float32, Enum,
    RawBytes, String, GenericVector, ParserError)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN
from hachoir_core.text_handler import humanFilesize, hexadecimal

MAX_ENVPOINTS = 32

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

class ModplugBlock(FieldSet):
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

def ParseModplugMetadata(s):
    while not s.eof:
        block = ModplugBlock(s, "block[]")
        yield block
        if block["block_type"].value == "STPM":
            break

    # More undocumented stuff: date ?
    size = (s._size - s.absolute_address - s.current_size)//8
    if size > 0:
        yield RawBytes(s, "info", size)
