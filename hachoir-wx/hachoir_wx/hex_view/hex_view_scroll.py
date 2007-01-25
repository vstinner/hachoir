# -*- coding: utf-8 -*-

from wx import ScrollBar, PreScrollBar

class hex_view_scroll_t(ScrollBar):
    def __init__(self):
        pre = PreScrollBar()
        self.PostCreate(pre)

    def ready(self):
        self.dispatcher.trigger('hex_view_scroll_ready', self)

