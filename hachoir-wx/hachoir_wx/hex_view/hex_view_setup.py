# -*- coding: utf-8 -*-

from hachoir_wx.resource import get_child_control
from hex_view_imp import hex_view_imp_t
from hex_view_fwd import hex_view_fwd_t
from hex_view_scroll_setup import setup_hex_view_scroll

def setup_hex_view(parent, dispatcher):
    print "[+] Setup hex view"
    hex_view = get_child_control(parent, 'hex_view')
    hex_view.ascii_view = get_child_control(parent, 'ascii_view')
    hex_view.addr_view = get_child_control(parent, 'addr_view')
    dispatcher.add_sender(hex_view)

    imp = hex_view_imp_t()
    dispatcher.add(imp)

    fwd = hex_view_fwd_t(imp)
    dispatcher.add_receiver(fwd)

    setup_hex_view_scroll(parent, dispatcher)

    return hex_view
