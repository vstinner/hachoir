# -*- coding: utf-8 -*-

import wx

class hex_view_fwd_t:
    def __init__(self, imp):
        self.imp = imp

    def on_hex_view_ready(self, dispatcher, view):
        assert view is not None

        view.Bind(wx.EVT_SIZE, self.on_resized)

    def on_resized(self, event):
        self.imp.on_resized()
