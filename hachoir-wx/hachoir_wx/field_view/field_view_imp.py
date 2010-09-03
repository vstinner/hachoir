# -*- coding: utf-8 -*-

from hachoir_wx.field_view.format import format_addr_hex, format_addr_dec, format_size, format_data, format_name, format_desc
from hachoir_core.i18n import _

MAXITEMS = 1000

class field_view_imp_t:
    def __init__(self):
        self.addr_func = lambda field: field._getAbsoluteAddress()
        self.format_addr = lambda field: format_addr_hex(self.addr_func(field))
        
        self.col_str_table = [
            lambda f: self.format_addr(f),          # address
            format_name,                            # name
            lambda f: f.getFieldType(),             # type
            lambda f: format_size(f._getSize()),    # size
            format_data,                            # data
            format_desc                             # description
        ]

    def on_field_set_ready(self, dispatcher, field_set):
        assert field_set is not None
        self.fields = field_set

    def on_field_view_ready(self, dispatcher, view):
        assert view is not None

        # register callbacks before activating the field view
        view.register_callback(cbGetItemText = self.OnGetItemTextImp)

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
        self.dispatcher.trigger('field_activated', field)

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
        field_count = 0
        for field in self.fields:
            field_count += 1
            if field_count > MAXITEMS:
                break

        if self.fields._getParent() is not None:
            self.has_parent = True
            self.view.SetItemCount(field_count + 1)
        else:
            self.has_parent = False
            self.view.SetItemCount(field_count)

        # autosize columns, based on a sample of the rows
        for col in xrange(self.view.get_col_count()):
            width = 0
            func = self.col_str_table[col]
            # when fields has more than 20 rows, they are probably similar.
            # Therefore this routine only checks the first 10 rows and last 10 rows.

            if field_count <= 20:
                field_range = [(0, field_count)]
            else:
                field_range = [(0, 10), (field_count - 10, field_count)]

            for begin, end in field_range:
                for i in xrange(begin, end):
                    width = max(width, len(func(self.fields[i])))

            self.view.resize_column(col, width)

    def OnGetItemTextImp(self, item, col):
        if self.has_parent:
            if item == 0:
                if col == self.view.get_col_index(_('name')):
                    return '../'
                else:
                    return ''
            else:
                item = item - 1
            parent_count = 1
        else:
            parent_count = 0
        try:
            self.fields[item+MAXITEMS]
            if item+MAXITEMS+parent_count > self.view.GetItemCount():
                self.view.SetItemCount(item+MAXITEMS+parent_count)
        except:
            if len(self.fields) + parent_count != self.view.GetItemCount():
                self.view.SetItemCount(len(self.fields)+parent_count)
        field = self.fields[item]
        return self.col_str_table[col](field)

    def refill_view(self):
        self.view.clear()
        self.fill_view()
