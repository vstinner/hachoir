# -*- coding: utf-8 -*-

from math import ceil
from stubs import byte_addr, get_file_size, get_page_num

class hex_view_scroll_imp_t:
    def on_file_ready(self, dispatcher, file):
        assert file is not None
        self.file = file

        self.reset_mappers()

    def on_hex_view_scroll_ready(self, dispatcher, view):
        assert view is not None
        self.view = view
        self.view.SetScrollbar(-1, -1, -1, -1)

    def on_hex_view_resized(self, dispatcher, view, pos):
        page_width = view.get_width_chars()
        page_height = view.get_height_chars()

        self.set_mappers(page_width)

        cur_height = self.offset_to_thumb(pos)
        total_height = int(ceil(get_file_size(self.file) / float(page_width)))

        self.view.SetScrollbar(cur_height, page_height, total_height, page_height)

    def on_field_selected(self, dispatcher, field):
        offset = byte_addr(field._getAbsoluteAddress())
        thumb = self.offset_to_thumb(offset)
        self.view.SetThumbPosition(thumb)

    def reset_mappers(self):
        self.thumb_to_offset = lambda thumb_pos: 0
        self.offset_to_thumb = lambda offset: 0

    def set_mappers(self, page_width):
        self.thumb_to_offset = lambda thumb_pos: thumb_pos * page_width
        self.offset_to_thumb = lambda offset: get_page_num(offset = offset,
                                                           page_width = page_width)

    def on_scrolled(self):
        offset = self.thumb_to_offset(self.view.GetThumbPosition())
        self.dispatcher.trigger('show_offset', offset)
