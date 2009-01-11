# -*- coding: utf-8 -*-

from wx import TextCtrl, TextAttr, PreTextCtrl
from stubs import to_ascii, to_hex, calc_char_range, calc_ascii_range, clamp_range
from hachoir_wx.hex_view import get_width_chars, get_height_chars

class hex_view_t(TextCtrl):
    default_style = TextAttr()
    default_style.SetBackgroundColour((255, 255, 255))
    default_style.SetTextColour((0, 0, 0))

    highlight_style = TextAttr()
    highlight_style.SetBackgroundColour((220, 220, 220))
    highlight_style.SetTextColour((52, 95, 215))

    def __init__(self):
        pre = PreTextCtrl()
        self.PostCreate(pre)

        self.get_width_chars = lambda: max(get_width_chars(self), 1)
        self.get_height_chars = lambda: max(get_height_chars(self), 1)

    def ready(self):
        self.dispatcher.trigger('hex_view_ready', self)

    def unmark(self):
        self.SetStyle(0, self.get_size(), self.default_style)
        self.ascii_view.SetStyle(0, self.get_ascii_size(), self.default_style)
        self.Refresh()

    def mark_range(self, start, size):
        mark_start, mark_end = calc_char_range(start, start + size, self.get_width_chars())

        mark_start = clamp_range(mark_start, 0, self.get_size())
        mark_end = clamp_range(mark_end, 0, self.get_size())

        self.SetStyle(mark_start, mark_end, self.highlight_style)
        self.Refresh()
        
        mark_start, mark_end = calc_ascii_range(start, start + size, self.get_width_chars())

        mark_start = clamp_range(mark_start, 0, self.get_ascii_size())
        mark_end = clamp_range(mark_end, 0, self.get_ascii_size())

        self.ascii_view.SetStyle(mark_start, mark_end, self.highlight_style)
        self.Refresh()

    def display_data(self, data):
        self.SetValue(to_hex(data, self.get_width_chars()))
        self.ascii_view.SetValue(to_ascii(data, self.get_width_chars()))

    def get_ascii_size(self):
        return len(self.ascii_view.GetValue())

    def get_size(self):
        return len(self.GetValue())

def get_page_size(view):
    return view.get_width_chars() * view.get_height_chars()
