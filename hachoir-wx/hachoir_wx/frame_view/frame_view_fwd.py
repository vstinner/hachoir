# -*- coding: utf-8 -*-

import wx

class frame_view_fwd_t:
    def __init__(self, imp):
        self.imp = imp

    def on_frame_view_ready(self, dispatcher, view):
        assert view is not None
        view.Bind(wx.EVT_ACTIVATE, self.on_activated)
        view.Bind(wx.EVT_SHOW, self.on_shown)

    def on_activated(self, event):
        if event.GetActive():
            self.imp.on_activated()

    def on_shown(self, event):
        if event.GetShow():
            self.imp.on_activated()
