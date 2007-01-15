"""
Extract metadata from RIFF file format: AVI video and WAV sound.
"""

from hachoir_metadata.metadata import Metadata, MultipleMetadata, registerExtractor
from hachoir_parser.container.riff import RiffFile
from hachoir_parser.video.fourcc import AUDIO_MICROSOFT_PCM, AUDIO_IEEE_FLOAT32
from hachoir_core.tools import humanFilesize
from hachoir_core.error import warning
from hachoir_core.i18n import _

class WavMetadata(Metadata):
    def extract(self, wav):
        format = wav["format"]

        # Number of channel, bits/sample, sample rate
        self.nb_channel = format["nb_channel"].value
        self.bits_per_sample = format["bit_per_sample"].value
        self.sample_rate = format["sample_per_sec"].value

        self.compression = format["codec"].display
        if "nb_sample/nb_sample" in wav:
            self.duration = float(wav["nb_sample/nb_sample"].value) * 1000 / self.sample_rate[0]
        if format["codec"].value in (AUDIO_MICROSOFT_PCM, AUDIO_IEEE_FLOAT32):
            # Codec with fixed bit rate
            self.bit_rate = self.nb_channel[0] * self.bits_per_sample[0] * self.sample_rate[0]
            if not hasattr(self, "duration"):
                self.duration = float(wav["audio_data/size"].value * 8) * 1000 / self.bit_rate[0]

class RiffMetadata(MultipleMetadata):
    tag_to_key = {
        "INAM": "title",
        "IART": "artist",
        "ICMT": "comment",
        "ICOP": "copyright",
        "IENG": "author",
        "ISFT": "producer",
        "ICRD": "creation_date"
    }

    def processChunk(self, chunk):
        if "text" not in chunk:
            return
        value = chunk["text"].value
        tag = chunk["tag"].value
        if tag not in self.tag_to_key:
            warning("Skip RIFF metadata %s: %s" % (tag, value))
            return
        key = self.tag_to_key[tag]
        setattr(self, key, value)

    def extract(self, riff):
        type = riff["type"].value
        if type == "WAVE":
            wav = WavMetadata()
            wav.extract(riff)
            self.addGroup("audio", wav, "Audio (WAV)")
        elif type == "AVI ":
            self.extractAVI(riff)
        if "info" in riff:
            self.extractInfo(riff["info"])

    def extractInfo(self, fieldset):
        for field in fieldset:
            if not field.is_field_set:
                continue
            if "tag" in field:
                if field["tag"].value == "LIST":
                    self.extractInfo(field)
                else:
                    self.processChunk(field)

    def extractAVIVideo(self, video):
        meta = Metadata()
        header = video["stream_hdr"]

        meta.compression = "%s (fourcc:\"%s\")" \
            % (header["fourcc"].display, header["fourcc"].value)
        if header["rate"].value and header["scale"].value:
            meta.frame_rate = float(header["rate"].value) / header["scale"].value
            self.duration = meta.duration = header["length"].value * 1000 / meta.frame_rate[0]

        if "stream_fmt/width" in video:
            format = video["stream_fmt"]
            meta.width = format["width"].value
            meta.height = format["height"].value
            meta.bits_per_pixel = format["depth"].value
        else:
            meta.width = header["right"].value - header["left"].value
            meta.height = header["bottom"].value - header["top"].value
        self.addGroup("video", meta, "Video stream")

    def extractAVIAudio(self, audio):
        if "stream_fmt" not in audio:
            return None
        meta = Metadata()
        format = audio["stream_fmt"]
        meta.nb_channel = format["channel"].value
        meta.sample_rate = format["sample_rate"].value
        header = audio["stream_hdr"]
        if header["rate"].value and header["scale"].value:
            frame_rate = float(header["rate"].value) / header["scale"].value
            meta.duration = header["length"].value * 1000 / frame_rate
        if header["fourcc"].value != "":
            meta.compression = "%s (fourcc:\"%s\")" \
                % (format["codec"].display, header["fourcc"].value)
        else:
            meta.compression = format["codec"].display
        return meta

    def useAviHeader(self, header):
        self.width = header["width"].value
        self.height = header["height"].value
        microsec = header["microsec_per_frame"].value
        if microsec:
            self.frame_rate = 1000000.0 / microsec
            if "total_frame" in header and header["total_frame"].value:
                self.duration = header["total_frame"].value * microsec / 1000

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
                    self.extractAVIVideo(stream)
                    have_video_info = True
                elif stream_type == "auds":
                    meta = self.extractAVIAudio(stream)
                    self.addGroup("audio[%u]" % audio_index, meta, "Audio stream")
                    audio_index += 1
            if not have_video_info and "avi_hdr" in headers:
                self.useAviHeader(headers["avi_hdr"])

        # Video has index?
        if "index" in avi:
            self.comment = _("Has audio/video index (%s)") \
                % humanFilesize(avi["index"].size/8)

registerExtractor(RiffFile, RiffMetadata)

