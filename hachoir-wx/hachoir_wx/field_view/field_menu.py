# -*- coding: utf-8 -*-

from hachoir_wx.dialogs import file_save_dialog
import wx

class field_menu_t:
    def __init__(self, parent, menu):
        self.parent = parent
        self.menu = menu

        # forward this call because xrc doesn't allow menu
        # subclassing (as of 2.6.3)
        self.Bind = self.menu.Bind

    def show_opts(self):
        self.parent.PopupMenu(self.menu)

    def ask_for_dump_file(self, title):
        dump_dlog = file_save_dialog(title)        
        if wx.ID_OK == dump_dlog.ShowModal():
            return dump_dlog.GetPath()

