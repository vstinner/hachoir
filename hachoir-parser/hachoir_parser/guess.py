"""
Parser list managment:
- loadParsers() load all parsers ;
- getParsersByStream() find the best parser for a binary stream ;
- createParser() find the best parser for a file.
"""

import os
import types
from hachoir_core.error import warning, info, HachoirError, HACHOIR_ERRORS
from hachoir_parser import Parser
from hachoir_core.stream import FileInputStream, InputSubStream
from hachoir_core.i18n import _
from hachoir_core.tools import makePrintable
from hachoir_core import config
from hachoir_core.editor import createEditor as createEditorFromParser

_hachoir_parsers_list = None

### Parser list ################################################################

def validParser(parser):
    # Check tags attribute
    if not hasattr(parser, "tags"):
        return "No tags attribute (tags)"
    if not parser.tags.get("description", ""):
        return "Empty description (description)"
    if not parser.tags.get("min_size", 0):
        return "Nul minimum size (min_size)"
    if "mime" in parser.tags and not isinstance(parser.tags["mime"], (list, tuple)):
        return "MIME type (mime) have to be a list or tuple"
    if "file_ext" in parser.tags and not isinstance(parser.tags["file_ext"], (list, tuple)):
        return "File extensions (file_ext) have to be a list or tuple"
    return ""

def loadParsers():
    """
    Load all parsers from "hachoir.parser" module.

    Return the list of loaded parsers.
    """
    global _hachoir_parsers_list

    # Parser list is already loaded?
    if _hachoir_parsers_list:
        return _hachoir_parsers_list

    _hachoir_parsers_list = []
    todo = []
    module = __import__("hachoir_parser")
    for attrname in dir(module):
        attr = getattr(module, attrname)
        if isinstance(attr, types.ModuleType):
            parser = attr
            todo.append(attr)

    for module in todo:
        attributes = ( getattr(module, name) for name in dir(module) )
        parsers = list( attr for attr in attributes \
            if isinstance(attr, type) \
               and issubclass(attr, Parser) \
               and hasattr(attr, "tags"))
        for parser in parsers:
            err = validParser(parser)
            if err:
                raise HachoirError("Invalid parser %s: %s" % (parser.__name__, err))
        _hachoir_parsers_list.extend(parsers)
    assert 1 <= len(_hachoir_parsers_list)
    return _hachoir_parsers_list

def printParserList(parser_list=None, title=None):
    """Display a list of parser with its title
     * title : title of the list to display
     * parser_list : list of parser (default get from loadParser())
    """

    if title:
        print title
    else:
        print _("List of Hachoir parsers.")

    # Get parser list (if not specified)
    if not parser_list:
        parser_list = loadParsers()

    # Create parser list sorted by module
    parsers_by_module = {}
    for parser in parser_list:
        module = parser.__module__.split(".")[1]
        if module in parsers_by_module:
            parsers_by_module[module].append(parser)
        else:
            parsers_by_module[module] = [parser]
    for module in sorted(parsers_by_module):
        print "\n[%s]" % module
        for parser in parsers_by_module[module]:
            text = ["- "]
            mimes = parser.tags.get("mime", ())
            if not isinstance(mimes, str):
                if len(mimes):
                    mimes = ", ".join(mimes)
                    text.append(mimes)
                    text.append(": ")
                else:
                    mimes = "(no mime type)"
            text.append(parser.tags["description"])
            print "".join(text)
    print

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

def _guessParsers(stream, file_ext=None, force_mime=None):
    parser_list = loadParsers()

    # Filter by minimum size
    parser_list = [ parser for parser in parser_list \
        if "min_size" not in parser.tags or stream.sizeGe(parser.tags["min_size"]) ]

    # Guess my MIME type
    if force_mime:
        ok, result = _guessParserByTag(stream, parser_list,
            "mime", force_mime, validate=False)
        if ok:
            return result
        else:
            parser_list = result

    # Guess by file extension
    if file_ext:
        ok, result = _guessParserByTag(stream, parser_list, "file_ext", file_ext)
        if ok:
            return result
        else:
            parser_list = result

    # Guess other parser
    for cls in parser_list:
        if config.debug:
            info(_("Guess parser: %s") % cls.__name__)
        parser, error_msg = parseStream(cls, stream, True)
        if parser:
            return parser
        else:
            info(_("Skip parser %s: %s") % (cls.__name__, error_msg))
    return None

def guessParser(stream, filename=None, force_mime=None):
    """
    Choose the best parser for the specified stream. Optional argument
    helping the choice:

     * filename: only file extension will be used
     * force_mime: try parser which match given MIME type before the others

    Returns the parser or None on error. May display info/warning on error.
    """
    file_ext = None
    if filename:
        # Extract file extension
        filename = os.path.basename(filename)
        filename = filename.split(".")
        if 1 < len(filename):
            file_ext = filename[-1]
    return _guessParsers(stream, file_ext=file_ext, force_mime=force_mime)

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
    # Load parsers (do nothing if function has already been call)
    loadParsers()

    # Create input stream
    stream = FileInputStream(filename, real_filename)
    if offset or size:
        if offset:
            offset *= 8
        else:
            offset = 0
        if size:
            size *= 8
        stream = InputSubStream(stream, offset, size)

    # Create field set
    if real_filename:
        filename = real_filename
    if offset:
        filename = None
    field_set = guessParser(stream, filename, force_mime=force_mime)
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

