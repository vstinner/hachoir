# -*- coding: utf-8 -*-

import wx

class core_type_menu_fwd_t:
    def __init__(self, imp):
        self.imp = imp

    def on_field_menu_ready(self, dispatcher, view):
        assert view is not None
        view.Bind(wx.EVT_MENU, self.on_type_selected)

    def on_type_selected(self, event):
        try:
            self.imp.on_type_selected(event.GetId())
        except KeyError:
            event.Skip()
