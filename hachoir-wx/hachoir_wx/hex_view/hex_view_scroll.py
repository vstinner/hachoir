# -*- coding: utf-8 -*-

import wx, wx.xrc

class hex_view_scroll_t(wx.ScrollBar):
    def __init__(self):
        pre = wx.PreScrollBar()
        self.PostCreate(pre)
        
    def ready(self):
        self.dispatcher.trigger('hex_view_scroll_ready', self)
        
