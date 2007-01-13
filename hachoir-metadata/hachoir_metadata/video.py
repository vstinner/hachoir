from hachoir_core.field import MissingField
from hachoir_core.error import HachoirError
from hachoir_metadata.metadata import Metadata, MultipleMetadata, registerExtractor
from hachoir_parser.video import MovFile, AsfFile, FlvFile
from hachoir_parser.container import MkvFile
from hachoir_core.i18n import _

class MkvMetadata(MultipleMetadata):
    tag_key = {
        "TITLE": "title",
        "URL": "url",
        "COPYRIGHT": "copyright",

        # TODO: use maybe another name?
        # Its value may be different than (...)/Info/DateUTC/date
        "DATE_RECORDED": "creation_date",

        # TODO: Extract subtitle metadata
        "SUBTITLE": "subtitle_author",
    }

    def extract(self, mkv):
        if "Segment[0]" not in mkv:
            raise HachoirError(_("Invalid Matroska video"))
        for segment in mkv.array("Segment"):
            self.processSegment(segment)

    def processSegment(self, segment):
        for field in segment:
            if field.name.startswith("Info["):
                self.processInfo(field)
            elif field.name.startswith("Tags["):
                for tag in field.array("Tag"):
                    self.processTag(tag)
            elif field.name.startswith("Tracks["):
                self.processTracks(field)

    def processTracks(self, tracks):
        for entry in tracks.array("TrackEntry"):
            self.processTrack(entry)

    def processTrack(self, track):
        if "TrackType/enum" not in track:
            return
        if track["TrackType/enum"].display == "video":
            self.processVideo(track)
        elif track["TrackType/enum"].display == "audio":
            self.processAudio(track)
        elif track["TrackType/enum"].display == "subtitle":
            self.processSubtitle(track)

    def trackCommon(self, track, meta):
        if "Name/unicode" in track:
            meta.title = track["Name/unicode"].value
        if "Language/string" in track \
        and track["Language/string"].value not in ("mis", "und"):
            meta.language = track["Language/string"].display

    def processVideo(self, track):
        video = Metadata()
        try:
            self.trackCommon(track, video)
            video.compression = track["CodecID/string"].value
            if "Video" in track:
                video.width = track["Video/PixelWidth/unsigned"].value
                video.height = track["Video/PixelHeight/unsigned"].value
        except MissingField:
            pass
        self.addGroup("video[]", video, "Video stream")

    def processAudio(self, track):
        audio = Metadata()
        try:
            self.trackCommon(track, audio)
            if "Audio" in track:
                audio.sample_rate = track["Audio/SamplingFrequency/float"].value
                audio.nb_channel = track["Audio/Channels/unsigned"].value
            audio.compression = track["CodecID/string"].value
        except MissingField:
            pass
        self.addGroup("audio[]", audio, "Audio stream")

    def processSubtitle(self, track):
        sub = Metadata()
        try:
            self.trackCommon(track, sub)
            sub.compression = track["CodecID/string"].value
        except MissingField:
            pass
        self.addGroup("subtitle[]", sub, "Subtitle")

    def processTag(self, tag):
        for field in tag.array("SimpleTag"):
            self.processSimpleTag(field)

    def processSimpleTag(self, tag):
        if "TagName/unicode" not in tag \
        or "TagString/unicode" not in tag:
            return
        name = tag["TagName/unicode"].value
        if name not in self.tag_key:
            return
        key = self.tag_key[name]
        value = tag["TagString/unicode"].value
        setattr(self, key, value)

    def processInfo(self, info):
        if "Duration/float" in info and "TimecodeScale/unsigned" in info:
            self.duration = (info["Duration/float"].value * info["TimecodeScale/unsigned"].value) / 1000000
        if "DateUTC/date" in info:
            self.creation_date = info["DateUTC/date"].display
        if "WritingApp/unicode" in info:
            self.producer = info["WritingApp/unicode"].value
        if "MuxingApp/unicode" in info:
            self.producer = info["MuxingApp/unicode"].value
        if "Title/unicode" in info:
            self.title = info["Title/unicode"].value

class FlvMetadata(MultipleMetadata):
    def extract(self, flv):
        if "audio[0]" in flv:
            meta = Metadata()
            audio = flv["audio[0]"]
            meta.sample_rate = audio["sampling_rate"].display
            # audio["is_16bit"].value
            if "mp3_frame" in audio:
                meta.compression = audio["mp3_frame"].description
            else:
                meta.compression = audio["codec"].display

            if audio["is_stereo"].value:
                meta.nb_channel = 2
            else:
                meta.nb_channel = 1
            self.addGroup("audio", meta)
        if "video[0]" in flv:
            meta = Metadata()
            video = flv["video[0]"]
            meta.compression = video["codec"].display
            self.addGroup("video", meta)
        # TODO: Computer duration
        # One technic: use last video/audio chunk and use timestamp
        # But this is very slow
        self.format_version = flv.description

        if "metadata/entry[1]" in flv:
            self.extractAMF(flv["metadata/entry[1]"])

    def extractAMF(self, amf):
        for entry in amf.array("item"):
            key = entry["key"].value
            if key == "duration":
                self.duration = entry["value"].value * 1000
            elif key == "creator":
                self.producer = entry["value"].value
            elif key == "audiosamplerate":
                self.sample_rate = entry["value"].value
            elif key == "framerate":
                self.frame_rate = entry["value"].value
            elif key == "metadatacreator":
                self.producer = entry["value"].value
            elif key == "metadatadate":
                self.creation_date = entry.value
            elif key == "width":
                self.width = int(entry["value"].value)
            elif key == "height":
                self.height = int(entry["value"].value)

class MovMetadata(Metadata):
    def extract(self, mov):
        for atom in mov:
            if "movie" in atom:
                self.processMovie(atom["movie"])

    def processMovieHeader(self, hdr):
        self.duration = hdr["duration"].value * 1000 / hdr["time_scale"].value
        self.creation_date = hdr["creat_date"].display
        self.last_modification = hdr["lastmod_date"].display
        self.comment = _("Play speed: %.1f%%") % (hdr["play_speed"].value*100)
        self.comment = _("User volume: %.1f%%") % (float(hdr["volume"].value)*100//255)

    def processMovie(self, atom):
        for field in atom:
            if "movie_hdr" in field:
                self.processMovieHeader(field["movie_hdr"])

class AsfMetadata(MultipleMetadata):
    def extract(self, asf):
        if "header/content" in asf:
            self.processHeader(asf["header/content"])

    def processHeader(self, header):
        compression = []
        bit_rates = []

        if "file_prop/content" in header:
            prop = header["file_prop/content"]
            self.creation_date = prop["creation_date"].display
            self.duration = prop["play_duration"].display
            if prop["seekable"]:
                self.comment = "Is seekable"
            self.comment = "Max bit rate: %s" % prop["max_bitrate"].display

        if "ext_desc/content" in header:
            for desc in header.array("ext_desc/content/descriptor"):
                self.comment = "%s=%s" % (desc["name"].value, unicode(desc["value"].value))

        if "codec_list/content" in header:
            for codec in header.array("codec_list/content/codec"):
                if "name" in codec:
                    text = codec["name"].value
                    if "desc" in codec and codec["desc"].value:
                        text = "%s (%s)" % (text, codec["desc"].value)
                    compression.append(text)

        audio_index = 1
        video_index = 1
        for index, stream_prop in enumerate(header.array("stream_prop")):
            if "content/audio_header" in stream_prop:
                audio = stream_prop["content/audio_header"]
                meta = self.streamProperty(header, index)
                if not hasattr(meta, "compression"):
                    meta.compression = audio["twocc"].display
                meta.sample_rate = audio["sample_rate"].value
                meta.bits_per_sample = audio["bits_per_sample"].value
                self.addGroup("audio[%u]" % audio_index, meta, "Audio stream #%u" % audio_index)
                audio_index += 1
            elif "content/video_header" in stream_prop:
                video = stream_prop["content/video_header"]
                meta = self.streamProperty(header, index)
                meta.width = video["width"].value
                meta.height = video["height"].value
                if "bmp_info" in video:
                    bmp_info = video["bmp_info"]
                    if not hasattr(meta, "compression"):
                        meta.compression = bmp_info["codec"].display
                    meta.bits_per_pixel = bmp_info["bpp"].value
                self.addGroup("video[%u]" % video_index, meta, "Video stream #%u" % video_index)
                video_index += 1

        if "metadata/content" in header:
            info = header["metadata/content"]
            try:
                self.title = info["title"].value
                self.author = info["author"].value
                self.copyright = info["copyright"].value
            except MissingField:
                pass

    def streamProperty(self, header, index):
        meta = Metadata()
        key = "bit_rates/content/bit_rate[%u]/avg_bitrate" % index
        if key in header:
            meta.bit_rate = header[key].value

        # TODO: Use codec list
        # It doesn't work when the video uses /header/content/bitrate_mutex
        # since the codec list are shared between streams but... how is it
        # shared?
#        key = "codec_list/content/codec[%u]" % index
#        if key in header:
#            codec = header[key]
#            if "name" in codec:
#                text = codec["name"].value
#                if "desc" in codec and codec["desc"].value:
#                    meta.compression = "%s (%s)" % (text, codec["desc"].value)
#                else:
#                    meta.compression = text
        return meta

registerExtractor(MovFile, MovMetadata)
registerExtractor(AsfFile, AsfMetadata)
registerExtractor(FlvFile, FlvMetadata)
registerExtractor(MkvFile, MkvMetadata)

