# -*- coding: utf-8 -*-

from hachoir_wx.resource import get_child_control
from hex_view_scroll_fwd import hex_view_scroll_fwd_t
from hex_view_scroll_imp import hex_view_scroll_imp_t

def setup_hex_view_scroll(parent, dispatcher):
    scroll = get_child_control(parent, 'hex_view_scroll')
    dispatcher.add_sender(scroll)

    imp = hex_view_scroll_imp_t()
    dispatcher.add(imp)

    fwd = hex_view_scroll_fwd_t(imp)
    dispatcher.add_receiver(fwd)

    scroll.ready()

    return scroll
