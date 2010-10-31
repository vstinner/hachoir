# -*- coding: utf-8 -*-

from hachoir_wx.field_view.stubs import save_substream_to_disk
from hachoir_core.i18n import _

class field_menu_imp_t:
    def on_field_set_ready(self, dispatcher, fields):
        assert fields is not None
        self.fields = fields
        self.selected = None

    def on_field_menu_ready(self, dispatcher, view):
        assert view is not None
        self.view = view

    def on_field_show_ops(self, dispatcher, field):
        self.view.show_opts()

    def on_addr_rel(self, event):
        self.dispatcher.trigger('address_relative')

    def on_addr_abs(self, event):
        self.dispatcher.trigger('address_absolute')

    def on_addr_hex(self, event):
        self.dispatcher.trigger('address_hexadecimal')

    def on_addr_dec(self, event):
        self.dispatcher.trigger('address_decimal')

    def on_split_bits(self):
        self.dispatcher.trigger('field_split_bits')

    def on_split_bytes(self):
        self.dispatcher.trigger('field_split_bytes')

    def on_field_selected(self, dispatcher, field):
        self.selected = field

    def on_file_ready(self, dispatcher, file):
        self.file = file

    def on_parse_substream(self, dispatcher):
        self.dispatcher.trigger('field_parse_substream', self.selected)

    def on_open_window_here(self, dispatcher):
        self.dispatcher.trigger('field_open_window_here', self.selected)

    def on_dump_to_disk(self, event):
        dump_path = self.view.ask_for_dump_file(_('Dump "' + self.selected._getPath() + '" To Disk...'))
        if dump_path is not None:
            save_substream_to_disk(self.selected, dump_path)

