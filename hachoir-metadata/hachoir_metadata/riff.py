"""
Extract metadata from RIFF file format: AVI video and WAV sound.
"""

from hachoir_metadata.metadata import Metadata, MultipleMetadata, registerExtractor
from hachoir_metadata.safe import fault_tolerant, getValue
from hachoir_parser.container.riff import RiffFile
from hachoir_parser.video.fourcc import UNCOMPRESSED_AUDIO
from hachoir_core.tools import humanFilesize, makeUnicode, timedelta2seconds
from hachoir_core.i18n import _
from hachoir_metadata.audio import computeComprRate as computeAudioComprRate
from datetime import timedelta

class RiffMetadata(MultipleMetadata):
    TAG_TO_KEY = {
        "INAM": "title",
        "IART": "artist",
        "ICMT": "comment",
        "ICOP": "copyright",
        "IENG": "author",
        "ISFT": "producer",
        "ICRD": "creation_date",
    }

    def extract(self, riff):
        type = riff["type"].value
        if type == "WAVE":
            self.extractWAVE(riff)
            size = getValue(riff, "audio_data/size")
            if size:
                computeAudioComprRate(self, size*8)
        elif type == "AVI ":
            self.extractAVI(riff)
        if "info" in riff:
            self.extractInfo(riff["info"])

    def processChunk(self, chunk):
        if "text" not in chunk:
            return
        value = chunk["text"].value
        tag = chunk["tag"].value
        if tag not in self.TAG_TO_KEY:
            self.warning("Skip RIFF metadata %s: %s" % (tag, value))
            return
        key = self.TAG_TO_KEY[tag]
        setattr(self, key, value)

    @fault_tolerant
    def extractWAVE(self, wav):
        format = wav["format"]

        # Number of channel, bits/sample, sample rate
        self.nb_channel = format["nb_channel"].value
        self.bits_per_sample = format["bit_per_sample"].value
        self.sample_rate = format["sample_per_sec"].value

        self.compression = format["codec"].display
        if "nb_sample/nb_sample" in wav \
        and 0 < format["sample_per_sec"].value:
            self.duration = timedelta(seconds=float(wav["nb_sample/nb_sample"].value) / format["sample_per_sec"].value)
        if format["codec"].value in UNCOMPRESSED_AUDIO:
            # Codec with fixed bit rate
            self.bit_rate = format["nb_channel"].value * format["bit_per_sample"].value * format["sample_per_sec"].value
            if not self.has("duration") \
            and "audio_data/size" in wav \
            and self.has("bit_rate"):
                duration = float(wav["audio_data/size"].value)*8 / self.get('bit_rate')
                self.duration = timedelta(seconds=duration)

    def extractInfo(self, fieldset):
        for field in fieldset:
            if not field.is_field_set:
                continue
            if "tag" in field:
                if field["tag"].value == "LIST":
                    self.extractInfo(field)
                else:
                    self.processChunk(field)

    def extractAVIVideo(self, header, meta):
        meta.compression = "%s (fourcc:\"%s\")" \
            % (header["fourcc"].display, makeUnicode(header["fourcc"].value))
        if header["rate"].value and header["scale"].value:
            fps = float(header["rate"].value) / header["scale"].value
            meta.frame_rate = fps
            if 0 < fps:
                self.duration = meta.duration = timedelta(seconds=float(header["length"].value) / fps)

        if "../stream_fmt/width" in header:
            format = header["../stream_fmt"]
            meta.width = format["width"].value
            meta.height = format["height"].value
            meta.bits_per_pixel = format["depth"].value
        else:
            meta.width = header["right"].value - header["left"].value
            meta.height = header["bottom"].value - header["top"].value

    def extractAVIAudio(self, format, meta):
        meta.nb_channel = format["channel"].value
        meta.sample_rate = format["sample_rate"].value
        meta.bit_rate = format["bit_rate"].value * 8
        if "../stream_hdr" in format:
            header = format["../stream_hdr"]
            if header["rate"].value and header["scale"].value:
                frame_rate = float(header["rate"].value) / header["scale"].value
                meta.duration = timedelta(seconds=float(header["length"].value) / frame_rate)
            if header["fourcc"].value != "":
                meta.compression = "%s (fourcc:\"%s\")" \
                    % (format["codec"].display, header["fourcc"].value)
        if not meta.has("compression"):
            meta.compression = format["codec"].display

    @fault_tolerant
    def useAviHeader(self, header):
        microsec = header["microsec_per_frame"].value
        if microsec:
            self.frame_rate = 1000000.0 / microsec
            total_frame = getValue(header, "total_frame")
            if total_frame:
                try:
                    self.duration = timedelta(seconds=total_frame * microsec)
                except OverflowError:
                    # OverflowError: "days=1036668219; must have magnitude <= 999999999"
                    pass
        self.width = header["width"].value
        self.height = header["height"].value

    def extractAVI(self, avi):
        # Process (audio and video) streams
        if "headers" in avi:
            audio_index = 1
            headers = avi["headers"]
            have_video_info = False
            for stream in headers.array("stream"):
                if "stream_hdr/stream_type" not in stream:
                    continue
                stream_type = stream["stream_hdr/stream_type"].value
                if stream_type == "vids":
                    if "stream_hdr" in stream:
                        meta = Metadata(self)
                        self.extractAVIVideo(stream["stream_hdr"], meta)
                        self.addGroup("video", meta, "Video stream")
                        have_video_info = True
                elif stream_type == "auds":
                    if "stream_fmt" in stream:
                        meta = Metadata(self)
                        self.extractAVIAudio(stream["stream_fmt"], meta)
                        self.addGroup("audio[%u]" % audio_index, meta, "Audio stream")
                        audio_index += 1
            if not have_video_info and "avi_hdr" in headers:
                self.useAviHeader(headers["avi_hdr"])

        # Compute global bit rate
        if self.has("duration") and "movie/size" in avi:
            self.bit_rate = float(avi["movie/size"].value) * 8 / timedelta2seconds(self.get('duration'))

        # Video has index?
        if "index" in avi:
            self.comment = _("Has audio/video index (%s)") \
                % humanFilesize(avi["index"].size/8)

registerExtractor(RiffFile, RiffMetadata)

