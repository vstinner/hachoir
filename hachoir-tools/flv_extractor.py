#!/usr/bin/env python
"""
Extract audio from a FLV movie

Author: Victor Stinner
Creation date: 2006-11-06
"""
from hachoir_parser import createParser
from hachoir_core.stream import FileOutputStream
from hachoir_core.i18n import getTerminalCharset
from hachoir_parser.video.flv import AUDIO_CODEC_MP3
import sys

def main():
    if len(sys.argv) != 2:
        print >>sys.stderr, "usage: %s input" % sys.argv[0]

    # Open input video
    inputname = unicode(sys.argv[1], getTerminalCharset())
    parser = createParser(inputname)
    if parser["audio[0]/codec"].value != AUDIO_CODEC_MP3:
        print >>sys.stderr, "Unknown audio codec: %s" % parser["audio[0]/codec"].display

    # Extract audio
    print "Extractor audio from: %s" % inputname
    outputname = inputname + ".mp3"
    output = FileOutputStream(outputname)
    for chunk in parser.array("audio"):
        data = chunk["music_data"]
        output.copyBitsFrom(data.parent.stream, data.absolute_address, data.size, data.parent.endian)
    print "Write audio into: %s" % outputname

main()

