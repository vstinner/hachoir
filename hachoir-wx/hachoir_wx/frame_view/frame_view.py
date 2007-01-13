# -*- coding: utf-8 -*-

import wx, wx.xrc

class frame_view_t(wx.Frame):
    def __init__(self):
        pre = wx.PreFrame()
        self.PostCreate(pre)

    def ready(self):
        self.dispatcher.trigger('frame_view_ready', self)

