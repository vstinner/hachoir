"""
Parser list managment:
- getParsersByStream() find the best parser for a binary stream ;
- createParser() find the best parser for a file.
"""

import os
from hachoir_core.error import error, warning, info, HACHOIR_ERRORS
from hachoir_parser import Parser, HachoirParserList
from hachoir_core.stream import FileInputStream, InputSubStream
from hachoir_core.i18n import _
from hachoir_core.tools import makePrintable
from hachoir_core import config
from hachoir_core.editor import createEditor as createEditorFromParser

### Parse a stream #############################################################

def _doCreateParser(cls, stream, validate):
    parser = cls(stream)
    if not validate:
        return (parser, None)
    result = parser.validate()
    if result is True:
        return (parser, None)
    if isinstance(result, str):
        result = makePrintable(result, "ASCII", to_unicode=True)
        message = _("validate() error: %s") % (result)
    else:
        message = _("validate() error")
    return (None, message)

def parseStream(cls, stream, validate=True):
    """
    Run a parser on a stream.

    Returns:
     * (None, error) on error where error is an unicode string ;
     * (parser, None) otherwise.
    """
    # Disable autofix during test
    autofix = config.autofix
    config.autofix = False
    try:
        parser, error_msg = _doCreateParser(cls, stream, validate)
    except HACHOIR_ERRORS, err:
        parser = None
        error_msg = unicode(err)
    config.autofix = autofix
    return (parser, error_msg)

### Guess parser for a stream ##################################################

def _matchTag(valid, file_ext):
    file_ext = file_ext.lower()
    if isinstance(valid, (list, tuple)):
        for item in valid:
            if item.lower() == file_ext:
                return True
        return False
    else:
        return valid.lower() == file_ext

def _guessParserByTag(stream, parser_list, tag_name, tag_value, validate=True):
    next_try = []
    for cls in parser_list:
        if tag_name in cls.tags \
        and _matchTag(cls.tags[tag_name], tag_value):
            if config.debug:
                info(_("Guess parser: %s") % cls.__name__)
            parser, error_msg = parseStream(cls, stream, validate)
            if parser:
                return True, parser
            else:
                warning(_("Skip parser %s: %s") % (cls.__name__, error_msg))
        else:
            next_try.append(cls)
    return False, next_try

def guessParser(stream, force_mime=None):
    # Filter by minimum size
    parser_list = [ parser for parser in HachoirParserList()
        if "min_size" not in parser.tags or stream.sizeGe(parser.tags["min_size"]) ]

    # Guess by MIME type
    if force_mime:
        ok, result = _guessParserByTag(stream, parser_list, "mime", force_mime, False)
        if ok:
            return result
        parser_list = result

    # Guess using stream tags
    for tag in stream.tags:
        if tag[0] == "filename":
            filename = os.path.basename(tag[1]).split(".")
            if len(filename) <= 1:
                continue
            tag = "file_ext", filename[-1]
        ok, result = _guessParserByTag(stream, parser_list, *tag)
        if ok:
            return result
        parser_list = result

    # Guess other parser
    for cls in parser_list:
        if config.debug:
            info(_("Guess parser: %s") % cls.__name__)
        parser, error_msg = parseStream(cls, stream, True)
        if parser:
            return parser
        info(_("Skip parser %s: %s") % (cls.__name__, error_msg))
    return None

### Choose parser for a file ###################################################

def createParser(filename, force_mime=None, offset=None, size=None, real_filename=None):
    """
    Create a parser from a file or returns None on error.

    Options:
    - filename (unicode): Input file name ;
    - force_mime (string, optionnal): force a specific parser using a MIME type ;
    - offset (long, optionnal): offset in bytes of the input file ;
    - size (long): maximum size in bytes of the input file ;
    - real_filename (str|unicode): Real file name.
    """
    # Create input stream
    stream = FileInputStream(filename, real_filename)
    if offset or size:
        if size:
            size *= 8
        stream = InputSubStream(stream, 8 * max(0, offset), size)

    # Create field set
    if real_filename:
        filename = real_filename
    if offset:
        filename = None
    field_set = guessParser(stream, force_mime)
    return field_set

def createEditor(filename, force_mime=None, offset=None, size=None):
    """
    Create a editor from a file or returns None on error.

    Options:
    - filename (unicode): Input file name ;
    - force_mime (string, optionnal): force a specific parser using a MIME type ;
    - offset (long, optionnal): offset in bytes of the input file  ;
    - size (long): maximum size in bytes of the input file.
    """
    parser = createParser(filename, force_mime, offset, size)
    if parser:
        parser = createEditorFromParser(parser)
    return parser

