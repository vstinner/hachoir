from hachoir_core.field import MissingField, Field, Parser as GenericParser
from hachoir_core.error import HACHOIR_ERRORS, error
from hachoir_core.tools import makePrintable

class HachoirParser:
    """
    A parser is the root of all other fields. It create first level of fields
    and have special attributes and methods:
    - tags: dictionnary with keys:
      - "file_ext": classical file extensions (string or tuple of strings) ;
      - "mime": MIME type(s) (string or tuple of strings) ;
      - "description": String describing the parser.
    - endian: Byte order (L{BIG_ENDIAN} or L{LITTLE_ENDIAN}) of input data ;
    - stream: Data input stream (set in L{__init__()}).

    Default values:
    - size: Field set size will be size of input stream ;
    - mime_type: First MIME type of tags["mime"] (if it does exist,
      None otherwise).
    """

    def __init__(self):
        self._mime_type = None

    #--- Methods that can be overridden -------------------------------------
    def createDescription(self):
        """
        Create an Unicode description
        """
        return self.tags["description"]

    def createMimeType(self):
        """
        Create MIME type (string), eg. "image/png"

        If it returns None, "application/octet-stream" is used.
        """
        if "mime" in self.tags:
            return self.tags["mime"][0]
        return None

    def validate(self):
        """
        Check that the parser is able to parse the stream. Valid results:
        - True: stream looks valid ;
        - False: stream is invalid ;
        - str: string describing the error.
        """
        raise NotImplementedError()

    #--- Getter methods -----------------------------------------------------
    def _getDescription(self):
        if self._description is None:
            try:
                self._description = self.createDescription()
                if isinstance(self._description, str):
                    self._description = makePrintable(
                        self._description, "ISO-8859-1", to_unicode=True)
            except HACHOIR_ERRORS, err:
                error("Error getting description of %s: %s" \
                    % (self.path, unicode(err)))
                self._description = self.tags["description"]
        return self._description
    description = property(_getDescription,
    doc="Description of the parser")

    def _getMimeType(self):
        if not self._mime_type:
            self._mime_type = self.createMimeType()
            if not self._mime_type:
                self._mime_type = "application/octet-stream"
        return self._mime_type
    mime_type = property(_getMimeType)

    def createContentSize(self):
        return None
    def _getContentSize(self):
        if not hasattr(self, "_content_size"):
            try:
                self._content_size = self.createContentSize()
            except MissingField, err:
                error("Unable to compute %s content size: %s" % (self.__class__.__name__, err))
                self._content_size = None
        return self._content_size
    content_size = property(_getContentSize)

    def createFilenameSuffix(self):
        """
        Create filename suffix: "." + first value of self.tags["file_ext"],
        or None if self.tags["file_ext"] doesn't exist.
        """
        try:
            return "." + self.tags["file_ext"][0]
        except KeyError:
            return None
    def _getFilenameSuffix(self):
        if not hasattr(self, "_filename_suffix"):
            self._filename_extension = self.createFilenameSuffix()
        return self._filename_extension
    filename_suffix = property(_getFilenameSuffix)

class Parser(HachoirParser, GenericParser):
    def __init__(self, stream):
        GenericParser.__init__(self, stream, None)
        HachoirParser.__init__(self)

