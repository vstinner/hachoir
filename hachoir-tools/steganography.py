#!/usr/bin/python

from hachoir_editor import (createEditor as hachoirCreateEditor,
    NewFieldSet, EditableInteger, EditableString, EditableBytes)
from hachoir_core.stream import FileOutputStream
from hachoir_core.error import HachoirError
from hachoir_parser import createParser
from hachoir_parser.image import PngFile
from hachoir_parser.audio import MpegAudioFile
from sys import argv, stdin, stdout, stderr, exit
import zlib

class InjecterError(HachoirError):
    pass

class Injecter:
    def __init__(self, editor):
        self.editor = editor

    def getMaxSize(self):
        "None: no limit"
        raise NotImplementedError()
    def read(self):
        raise NotImplementedError()
    def write(self, data):
        raise NotImplementedError()
    def saveInto(self, filename):
        output = FileOutputStream(filename)
        self.editor.writeInto(output)

def computeCRC32(data):
    "Compute CRC-32 of data string. Result is a positive integer."
    crc = zlib.crc32(data)
    if 0 <= crc:
        return crc
    else:
        return 1 << 32

class PngInjecter(Injecter):
    MAGIC = "HACHOIR"

    def getMaxSize(self):
        return None
    def read(self):
        for field in self.editor:
            if field.name.startswith("text[") \
            and field["keyword"].value == self.MAGIC:
                return field["text"].value
        return None

    def write(self, data):
        tag = "tEXt"
        data = "%s\0%s" % (self.MAGIC, data)
        size = len(data)
        crc = computeCRC32(tag + data)
        chunk = NewFieldSet(self.editor, "inject[]")
        chunk.insert( EditableInteger(chunk, "size", False, 32, size) )
        chunk.insert( EditableBytes(chunk, "tag", tag) )
        chunk.insert( EditableBytes(chunk, "content", data) )
        chunk.insert( EditableInteger(chunk, "crc32", False, 32, crc) )
        self.editor.insertBefore("end", chunk)

class MpegAudioInjecter(Injecter):
    MAX_PACKET_SIZE = 2048  # bytes between each frame

    def __init__(self, editor, packet_size=None):
        Injecter.__init__(self, editor)
        self.frames = editor["frames"]
        if packet_size:
            # Limit packet size to 1..MAX_PACKET_SIZE bytes
            self.packet_size = max(min(self.MAX_PACKET_SIZE, packet_size), 1)
        else:
            self.packet_size = self.MAX_PACKET_SIZE

    def getMaxSize(self):
        return len(self.frames) * self.packet_size * 8

    def read(self):
        data = []
        for field in self.frames:
            if field.name.startswith("padding["):
                data.append(field.value)
        if data:
            return "".join(data)
        else:
            return None

    def write(self, data):
        count = 30
        self.packet_size = 3
        data = "\0" * (self.packet_size * count - 1)
        print "Packet size: %s" % self.packet_size
        print "Check input message"
        if "\xff" in data:
            raise InjecterError("Sorry, MPEG audio injecter disallows 0xFF byte")

#        print "Check message size"
#        maxbytes = self.getMaxSize()
#        if maxbytes < len(data)*8:
#            raise InjecterError("Message is too big (max: %s, want: %s)" % \
#                (maxbytes, len(data)))

        print "Inject message"
        field_index = 0
        index = 0
        output = self.frames
        while index < len(data):
            padding = data[index:index + self.packet_size]
            name = "frame[%u]" % field_index
            print "Insert %s before %s" % (len(padding), name)
            output.insertAfter(name,  EditableString(output, "padding[]", "fixed", padding) )
            index += self.packet_size
            field_index += 2


def createEditor(filename):
    parser = createParser(filename)
    return hachoirCreateEditor(parser)

injecter_cls = {
    PngFile: PngInjecter,
    MpegAudioFile: MpegAudioInjecter,
}

def main():
    if len(argv) != 2:
        print >>stderr, "usage: %s music.mp3" % argv[0]
        exit(1)

    filename = unicode(argv[1])
    editor = createEditor(filename)
#    injecter = injecter_cls[editor.input.__class__]
    injecter = MpegAudioInjecter(editor, packet_size=16)

    if False:
        data = injecter.read()
        if data:
            stdout.write(data)
            exit(0)
        else:
            print >>stderr, "No data"
            exit(1)
    else:
        out_filename = filename + ".msg"
        print "Write your message and valid with CTRL+D:"
        stdout.flush()
        data = stdin.read()

        print "Hide message"
        injecter.write(data)

        print "Write ouput into: %s" % out_filename
        injecter.saveInto(out_filename)

if __name__ == "__main__":
    main()

