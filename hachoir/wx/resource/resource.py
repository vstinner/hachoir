import os
from wx.xrc import XmlResource, XRCCTRL

def get_resource():
    filename = os.path.join(
        os.getcwd(), os.path.dirname(__file__), 'hachoir_wx.xrc')
    return XmlResource(filename)

def get_frame(name):
    return get_resource().LoadFrame(None, name)

def get_child_control(parent, child):
    return XRCCTRL(parent, child)

def get_menu(name):
    return get_resource().LoadMenu(name)
