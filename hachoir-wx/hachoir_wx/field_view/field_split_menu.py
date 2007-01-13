# -*- coding: utf-8 -*-

from wx import GetNumberFromUser
from hachoir_core.i18n import _

class field_split_menu_t:
    def __init__(self, parent, menu):
        self.parent = parent
        self.menu = menu
        self.Bind = self.menu.Bind # see note in field_menu.py

    def ask_split(self, caption, min, max):
        num = GetNumberFromUser(_('Enter split offset:'), '', 
                                caption, min, min, max, self.parent)

        if -1 == num:
            return None
        else:
            return num
