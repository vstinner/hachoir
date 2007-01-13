from hachoir_core.i18n import getTerminalCharset, _
from hachoir_core.stream import InputIOStream, InputStreamError
from cStringIO import StringIO

def StringInputStream(content, source="<string>"):
    inputio = StringIO(content)
    return InputIOStream(inputio, source, size=len(content)*8)


def FileInputStream(filename, real_filename=None):
    """
    Create an input stream of a file. filename must be unicode.

    real_filename is an optional argument used to specify the real filename,
    its type can be 'str' or 'unicode'. Use real_filename when you are
    not able to convert filename to real unicode string (ie. you have to
    use unicode(name, 'replace') or unicode(name, 'ignore')).
    """
    assert isinstance(filename, unicode)
    if not real_filename:
        real_filename = filename
    try:
        inputio = open(real_filename, 'rb')
    except IOError, err:
        charset = getTerminalCharset()
        errmsg = unicode(str(err), charset)
        raise InputStreamError(_("Unable to open file %s: %s")
            % (filename, errmsg))
    return InputIOStream(inputio, "file:%s" % filename)
