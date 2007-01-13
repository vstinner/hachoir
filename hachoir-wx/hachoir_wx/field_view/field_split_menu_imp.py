# -*- coding: utf-8 -*-

from hachoir_wx.field_view.mutator import split_field
from hachoir_core.field import RawBytes, RawBits
from hachoir_core.i18n import _

class field_split_menu_imp_t:
    def on_field_split_menu_ready(self, dispatcher, view):
        assert view is not None
        self.view = view

    def on_field_selected(self, dispatcher, field):
        self.field = field

    def on_split_bytes(self):
        if self.split_field(_('Split Bytes...'), self.field, RawBytes, lambda field: field._getSize() / 8):
            self.dispatcher.trigger('field_was_split_bytes', self.field)
    
    def on_split_bits(self):
        if self.split_field(_('Split Bits...'), self.field, RawBits, lambda field: field._getSize()):
            self.dispatcher.trigger('field_was_split_bits', self.field)

    def split_field(self, caption, field, split_type, size_func):
        offset = self.view.ask_split(caption, 1, size_func(field) - 1)
        if offset is not None:
            new_fields = split_field(field, offset, field._getName(), split_type, size_func)
            
        return offset
