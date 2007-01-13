# -*- coding: utf-8 -*-

from field_menu_imp import field_menu_imp_t
from field_menu_fwd import field_menu_fwd_t
from field_menu import field_menu_t

from core_type_menu import core_type_menu_t
from core_type_menu_fwd import core_type_menu_fwd_t
from core_type_menu_imp import core_type_menu_imp_t

from field_split_menu import field_split_menu_t
from field_split_menu_fwd import field_split_menu_fwd_t
from field_split_menu_imp import field_split_menu_imp_t

import wx

from hachoir_wx.resource import get_menu_bar, get_menu_from_bar

def setup_field_menu(parent, dispatcher):
    bar = get_menu_bar('context_menu_bar')
    menu = get_menu_from_bar(bar, 'Field')
    field_menu = field_menu_t(parent, menu)

    imp = field_menu_imp_t()
    dispatcher.add(imp)

    fwd = field_menu_fwd_t(imp)
    dispatcher.add_receiver(fwd)

    setup_core_type_menu(menu, dispatcher)
    setup_field_split_menu(parent, menu, dispatcher)

    dispatcher.trigger('field_menu_ready', field_menu)

    return field_menu

def setup_core_type_menu(parent, dispatcher):
    menu = parent.FindItemById(wx.xrc.XRCID('field_menu_convert_to_core_type')).GetSubMenu()
    core_type_menu = core_type_menu_t(menu)

    imp = core_type_menu_imp_t()
    dispatcher.add(imp)

    fwd = core_type_menu_fwd_t(imp)
    dispatcher.add_receiver(fwd)

    dispatcher.trigger('core_type_menu_ready', core_type_menu)

def setup_field_split_menu(parent, parent_menu, dispatcher):
    menu = parent_menu.FindItemById(wx.xrc.XRCID('field_menu_split')).GetSubMenu()
    split_menu = field_split_menu_t(parent, menu)

    imp = field_split_menu_imp_t()
    dispatcher.add(imp)

    fwd = field_split_menu_fwd_t(imp)
    dispatcher.add_receiver(fwd)

    dispatcher.trigger('field_split_menu_ready', split_menu)
