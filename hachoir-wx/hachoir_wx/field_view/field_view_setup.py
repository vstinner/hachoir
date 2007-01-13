# -*- coding: utf-8 -*-

from hachoir_wx.resource import get_child_control
from field_view_imp import field_view_imp_t
from field_view_fwd import field_view_fwd_t
from field_menu_setup import setup_field_menu

def setup_field_view(parent, dispatcher):
    print "[+] Setup field view"
    field_view = get_child_control(parent, 'field_view')
    dispatcher.add_sender(field_view)

    field_view_imp = field_view_imp_t()
    dispatcher.add(field_view_imp)

    field_view_fwd = field_view_fwd_t(field_view_imp)
    dispatcher.add(field_view_fwd)

    setup_field_menu(field_view, dispatcher)

    return field_view
