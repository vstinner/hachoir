# -*- coding: utf-8 -*-

from wx import EVT_MENU
from wx.xrc import XRCID

class field_menu_fwd_t:
    def __init__(self, imp):
        self.imp = imp

    def on_field_view_ready(self, dispatcher, view):
        assert view is not None

        view.Bind(EVT_MENU, self.imp.on_addr_rel,
                  id=XRCID('field_menu_address_relative'))
        view.Bind(EVT_MENU, self.imp.on_addr_abs,
                  id=XRCID('field_menu_address_absolute'))
        view.Bind(EVT_MENU, self.imp.on_addr_hex,
                  id=XRCID('field_menu_address_base_hex'))
        view.Bind(EVT_MENU, self.imp.on_addr_dec,
                  id=XRCID('field_menu_address_base_dec'))
        view.Bind(EVT_MENU, self.imp.on_dump_to_disk,
                  id=XRCID('field_menu_dump_to_disk'))
        view.Bind(EVT_MENU, self.imp.on_parse_substream,
                  id=XRCID('field_menu_parse_substream'))
        view.Bind(EVT_MENU, self.imp.on_open_window_here,
                  id=XRCID('field_menu_open_window_here'))

