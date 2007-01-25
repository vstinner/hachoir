# -*- coding: utf-8 -*-

import os
from wx.xrc import XmlResource, XRCCTRL

def get_resource():
    filename = os.path.join(os.getcwd(), os.path.dirname(__file__), 'hachoir_wx.xrc')
    return XmlResource(filename)

def get_frame(name):
    return get_resource().LoadFrame(None, name)

def get_child_control(parent, child):
    return XRCCTRL(parent, child)

def get_menu_bar(name):
    return get_resource().LoadMenuBar(name)

def get_menu_from_bar(menu_bar, menu_name):
    menu_index = menu_bar.FindMenu(menu_name)
    assert -1 != menu_index, 'cannot find menu ' + menu_name + ' in menu bar ' + menu_bar.GetTitle()
    return menu_bar.GetMenu(menu_index)

