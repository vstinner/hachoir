__version__ = "0.8.0"

from hachoir_parser.parser import Parser
from hachoir_parser.parser_list import ParserList, HachoirParserList
from hachoir_parser.guess import (guessParser,
    parseStream, createParser, createEditor)
from hachoir_parser import (archive, audio, container,
    file_system, image, game, misc, network, office, program, video)

