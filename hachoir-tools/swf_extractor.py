#!/usr/bin/python
from hachoir_core.cmd_line import unicodeFilename
from hachoir_parser import createParser, guessParser
from hachoir_parser.container.swf import SOUND_CODEC_MP3
from sys import stderr, exit, argv

class JpegExtractor:
    def __init__(self):
        self.jpg_index = 1
        self.snd_index = 1
        self.verbose = False

    def storeJPEG(self, content):
        name = "image-%03u.jpg" % self.jpg_index
        print "Write new image: %s" % name
        open(name, "w").write(content)
        self.jpg_index += 1

    def createNewSound(self):
        name = "sound-%03u.mp3" % self.snd_index
        print "Write new sound: %s" % name
        self.snd_index += 1
        return open(name, "w")

    def extractFormat2(self, field):
        if "jpeg_header" in field:
            header = field["jpeg_header"]
            if 32 < header.size:
                if self.verbose:
                    print "Use JPEG table: %s" % header.path
                header = field.root.stream.readBytes(header.absolute_address, (header.size-16)//8)
            else:
                header = ""
        else:
            header = None
        content = field["image"].value
        if header:
            content = header + content[2:]
        if self.verbose:
            print "Extract JPEG from %s" % field.path
        self.storeJPEG(content)

    def extractSound2(self, parser):
        header = None
        output = None
        for field in parser:
            if field.name.startswith("def_sound["):
                header = field
                output = self.createNewSound()
                data = header["music_data"].value
                assert data[0] == '\xFF'
                output.write(data)
            elif field.name.startswith("sound_blk") \
            and "music_data" in field:
                data = field["music_data"].value
                if data:
                    assert data[0] == '\xFF'
                    output.write(data)

    def main(self):
        if len(argv) != 2:
            print >>stderr, "usage: %s document.swf" % argv[0]
            exit(1)

        realname = argv[1]
        filename = unicodeFilename(realname)
        parser = createParser(filename, real_filename=realname)

        if parser["signature"].value == "CWS":
            deflate_swf = parser["compressed_data"].getSubIStream()
            parser = guessParser(deflate_swf)

        if "jpg_table/data" in parser:
            # JPEG pictures with common header
            jpeg_header = parser["jpg_table/data"].value[:-2]
            for field in parser.array("def_bits"):
                jpeg_content = field["image"].value[2:]
                if self.verbose:
                    print "Extract JPEG from %s" % field.path
                self.storeJPEG(jpeg_header + jpeg_content)

        # JPEG in format 2/3
        for field in parser.array("def_bits_jpeg2"):
            self.extractFormat2(field)
        for field in parser.array("def_bits_jpeg3"):
            self.extractFormat2(field)

        # Extract sound
        #self.extractSound(parser)
        self.extractSound2(parser)

        # Does it extract anything?
        if self.jpg_index == 1:
            print "No JPEG picture found."
        if self.snd_index == 1:
            print "No sound found."

JpegExtractor().main()

