# -*- coding: utf-8 -*-

from hachoir_wx.field_view.format import format_addr_hex, format_addr_dec, format_size, format_data, format_name, format_desc
from hachoir_core.i18n import _

class field_view_imp_t:
    def __init__(self):
        self.addr_func = lambda field: field._getAbsoluteAddress()
        self.format_addr = lambda field: format_addr_hex(self.addr_func(field))

    def on_field_set_ready(self, dispatcher, field_set):
        assert field_set is not None
        self.fields = field_set

    def on_field_view_ready(self, dispatcher, view):
        assert view is not None
        self.view = view
        self.fill_view()
        self.dispatcher.trigger('field_activated', self.fields)

    def on_item_selected(self):
        name = self.view.get_selected(_('name'))
        if isinstance(name, unicode):
            name = str(name)
        self.dispatcher.trigger('field_selected', self.fields[name])

    def on_item_activated(self):
        field = self.fields[self.view.get_selected(_('name'))]
        if field.is_field_set:
            self.fields = field
            self.refill_view()

            self.dispatcher.trigger('field_activated', self.fields)

    def on_field_modified(self, dispatcher, field):
        self.refill_view()

    def on_item_show_ops(self):
        field = self.fields[self.view.get_selected(_('name'))]
        self.dispatcher.trigger('field_show_ops', field)

    def on_address_relative(self, dispatcher):
        self.addr_func = lambda field: field._getAddress()
        self.refill_view()

    def on_address_absolute(self, dispatcher):
        self.addr_func = lambda field: field._getAbsoluteAddress()
        self.refill_view()

    def on_address_hexadecimal(self, dispatcher):
        self.format_addr = lambda field: format_addr_hex(self.addr_func(field))
        self.refill_view()

    def on_address_decimal(self, dispatcher):
        self.format_addr = lambda field: format_addr_dec(self.addr_func(field))
        self.refill_view()

    def on_field_was_split_bytes(self, dispatcher, field):
        self.refill_view()

    def on_field_was_split_bits(self, dispatcher, field):
        self.refill_view()

    def fill_view(self):
        if self.fields._getParent() is not None:
            self.view.append_row({ _('name') : '../' })

        for field in self.fields:
            map = {
                _('address') : self.format_addr(field),
                _('name') : format_name(field),
                _('type') : field.__class__.__name__,
                _('size') : format_size(field._getSize()),
                _('data') : format_data(field),
                _('description'): format_desc(field)
                }

            self.view.append_row(map)

    def refill_view(self):
        self.view.clear()
        self.fill_view()
