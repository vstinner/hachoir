"""
Functions to manage internationalisation (i18n):
- initLocale(): setup locales and install Unicode compatible stdout and
  stderr ;
- getTerminalCharset(): guess terminal charset ;
- gettext(text) translate a string to current language. The function always
  returns Unicode string. You can also use the alias: _() ;
- ngettext(singular, plural, count): translate a sentence with singular and
  plural form. The function always returns Unicode string.

WARNING: Loading this module indirectly calls initLocale() which sets
         locale LC_ALL to ''. This is needed to get user preferred locale
         settings.
"""

import hachoir_core.config as config
import hachoir_core
import locale
from os import path
import sys

def _getTerminalCharset():
    """
    Function used by getTerminalCharset() to get terminal charset.

    @see getTerminalCharset()
    """
    # (1) Try locale.getpreferredencoding()
    try:
        charset = locale.getpreferredencoding()
        if charset:
            return charset
    except (locale.Error, AttributeError):
        pass

    # (2) Try locale.nl_langinfo(CODESET)
    try:
        charset = locale.nl_langinfo(locale.CODESET)
        if charset:
            return charset
    except (locale.Error, AttributeError):
        pass

    # (3) Try sys.stdout.encoding
    if hasattr(sys.stdout, "encoding") and sys.stdout.encoding:
        return sys.stdout.encoding

    # (4) Otherwise, returns "ASCII"
    return "ASCII"

def getTerminalCharset():
    """
    Guess terminal charset using differents tests:
    1. Try locale.getpreferredencoding()
    2. Try locale.nl_langinfo(CODESET)
    3. Try sys.stdout.encoding
    4. Otherwise, returns "ASCII"

    WARNING: Call initLocale() before calling this function, or:
    >>> import locale
    >>> locale.setlocale(locale.LC_ALL, "")
    """
    try:
        return getTerminalCharset.value
    except AttributeError:
        getTerminalCharset.value = _getTerminalCharset()
        return getTerminalCharset.value

class UnicodeStdout:
    def __init__(self, old_device, charset):
        self.device = old_device
        self.charset = charset

    def flush(self):
        self.device.flush()

    def write(self, text):
        if isinstance(text, unicode):
            text = text.encode(self.charset, 'replace')
        self.device.write(text)

def initLocale():
    try:
        if initLocale.is_done:
            return
    except AttributeError:
        pass
    initLocale.is_done = True

    # Setup locales
    try:
        locale.setlocale(locale.LC_ALL, "")
    except (locale.Error, IOError):
        pass

    charset = getTerminalCharset()
    sys.stdout = UnicodeStdout(sys.stdout, charset)
    sys.stderr = UnicodeStdout(sys.stderr, charset)
    return charset

def _dummy_gettext(text):
    return unicode(text)

def _dummy_ngettext(singular, plural, count):
    if 1 < abs(count) or not count:
        return unicode(plural)
    else:
        return unicode(singular)

def _initGettext():
    charset = initLocale()

    # Try to load gettext module
    if config.use_i18n:
        try:
            import gettext
            ok = True
        except ImportError:
            ok = False
    else:
        ok = False

    # gettext is not available or not needed: use dummy gettext functions
    if not ok:
        return (_dummy_gettext, _dummy_ngettext)

    # Gettext variables
    package = hachoir_core.PACKAGE
    locale_dir = path.join(path.dirname(__file__), "..", "locale")

    # Initialize gettext module
    gettext.bindtextdomain(package, locale_dir)
    gettext.textdomain(package)
    translate = gettext.gettext
    ngettext = gettext.ngettext

    # TODO: translate_unicode lambda function really sucks!
    # => find native function to do that
    unicode_gettext = lambda text: \
        unicode(translate(text), charset)
    unicode_ngettext = lambda singular, plural, count: \
        unicode(ngettext(singular, plural, count), charset)
    return (unicode_gettext, unicode_ngettext)

# Initialize _(), gettext() and ngettext() functions
gettext, ngettext = _initGettext()
_ = gettext

