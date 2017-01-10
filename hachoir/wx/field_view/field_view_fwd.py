# -*- coding: utf-8 -*-

import wx

class field_view_fwd_t:
    def __init__(self, imp):
        self.imp = imp

    def on_field_view_ready(self, dispatcher, field_view):
        assert field_view is not None

        field_view.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.on_item_right_clicked)
        field_view.Bind(wx.EVT_RIGHT_UP, self.on_item_right_clicked)
        field_view.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        field_view.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)

    def on_item_activated(self, event):
        self.imp.on_item_activated()

    def on_item_selected(self, event):
        self.imp.on_item_selected()

    def on_item_right_clicked(self, event):
        self.imp.on_item_show_ops()
