# -*- coding: utf-8 -*-

import wx

def get_charset():
    try:
        charset = locale.getdefaultlocale()[1]
    except (locale.Error, NamError, AttributeError, IndexError):
        pass

    if charset is None:
        charset = sys.getdefaultencoding()

    return charset

def force_unicode(name):
    if not wx.USE_UNICODE:
        charset = get_charset()
        name = unicode(name, charset)

    return name
