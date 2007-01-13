# -*- coding: utf-8 -*-

import wx

class core_type_menu_t:
    def __init__(self, menu):
        self.menu = menu
        self.id_to_type = {}

        self.Bind = self.menu.Bind # see note in field_menu.py

    def add_type(self, type_name):
        type_id = wx.NewId()
        self.id_to_type[type_id] = type_name
        self.menu.Append(type_id, type_name)

    def get_type_name(self, id):
        return self.id_to_type[id]

    def clear(self):
        items = self.menu.GetMenuItems()
        for item in items:
            self.menu.DeleteItem(item) # TODO: what's the difference between Remove and Delete?
