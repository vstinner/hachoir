from hachoir_core.field import Field, FieldError

class ParserError(FieldError):
    """
    Error raised by a field set.

    @see: L{FieldError}
    """
    pass

class MatchError(FieldError):
    """
    Error raised by a field set when the stream content doesn't
    match to file format.

    @see: L{FieldError}
    """
    pass

class BasicFieldSet(Field):
    pass

