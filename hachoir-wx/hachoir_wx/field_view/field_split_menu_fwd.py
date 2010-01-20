# -*- coding: utf-8 -*-

import wx

class field_split_menu_fwd_t:
    def __init__(self, imp):
        self.imp = imp

    def on_field_menu_ready(self, dispatcher, view):
        assert view is not None

        view.Bind(wx.EVT_MENU, self.on_split_bytes,
          id = wx.xrc.XRCID('field_menu_split_bytes'))
        view.Bind(wx.EVT_MENU, self.on_split_bits,
          id = wx.xrc.XRCID('field_menu_split_bits'))

    def on_split_bits(self, event):
        self.imp.on_split_bits()

    def on_split_bytes(self, event):
        self.imp.on_split_bytes()

