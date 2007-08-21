# -*- coding: utf-8 -*-

import wx
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
    if not isinstance(name, unicode):
        charset = get_charset()
        name = unicode(name, charset)

    return name
