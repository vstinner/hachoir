# -*- coding: utf-8 -*-

import wx

class hex_view_scroll_fwd_t:
    def __init__(self, imp):
        self.imp = imp

    def on_hex_view_scroll_ready(self, dispatcher, view):
        assert view is not None
        view.Bind(wx.EVT_SCROLL, self.on_scrolled)

    def on_scrolled(self, event):
        self.imp.on_scrolled()
