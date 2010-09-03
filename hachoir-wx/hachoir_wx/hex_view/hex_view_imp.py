# -*- coding: utf-8 -*-

from hex_view import get_page_size
from stubs import clamp_range, byte_addr, safe_seek, calc_field_mark, get_page_offset

MAX_SIZE = 10 * 1024

class hex_view_imp_t:
    def on_file_ready(self, dispatcher, file):
        assert file is not None
        self.input = file
        self.field = None
        self.pos = 0
        self.format_addr = lambda addr: '%08x'%addr

    def on_hex_view_ready(self, dispatcher, view):
        assert view is not None
        self.view = view
        self.fill_view(0)

    def fill_view(self, pos):
        paged_pos = get_page_offset(pos, self.view.get_width_chars())

        if safe_seek(self.input, paged_pos):
            size = clamp_range(get_page_size(self.view), 1, MAX_SIZE)
            self.view.display_data(self.input.read(size))
            self.pos = paged_pos
            self.update_addr_view()

    def on_resized(self):
        self.fill_view(self.pos)
        self.update_mark()

        self.dispatcher.trigger('hex_view_resized', self.view, self.pos)

    def on_show_offset(self, dispatcher, pos):
        self.fill_view(pos)
        self.update_mark()

    def on_field_selected(self, dispatcher, field):
        self.fill_view(byte_addr(field._getAbsoluteAddress()))
        self.update_set_mark(field)

    def on_address_decimal(self, dispatcher):
        self.format_addr = lambda addr: '%08d'%addr
        self.update_addr_view()

    def on_address_hexadecimal(self, dispatcher):
        self.format_addr = lambda addr: '%08x'%addr
        self.update_addr_view()

    def update_addr_view(self):
        addr_text_list = []
        for i in xrange(self.view.get_height_chars()):
            addr_text_list.append( self.format_addr(self.pos+i*self.view.get_width_chars())+'\n')
        self.view.addr_view.SetValue(''.join(addr_text_list))

    def update_set_mark(self, field):
        self.field = field
        self.update_mark()

    def update_mark(self):
        if self.field:
            self.view.unmark()
            mark = calc_field_mark(self.pos, self.field)
            self.view.mark_range(mark[0], mark[1])
