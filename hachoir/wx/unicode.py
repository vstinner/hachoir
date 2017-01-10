import locale
import sys


def get_charset():
    try:
        charset = locale.getdefaultlocale()[1]
    except (locale.Error, NameError, AttributeError, IndexError):
        pass

    if charset is None:
        charset = sys.getdefaultencoding()

    return charset


def force_unicode(name):
    if not isinstance(name, str):
        charset = get_charset()
        name = str(name, charset)

    return name
