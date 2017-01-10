import os
from wx.xrc import XmlResource, XRCID


def get_resource():
    filename = os.path.join(os.getcwd(), os.path.dirname(__file__), 'hachoir_wx.xrc')
    return XmlResource(filename)


def get_frame(name):
    return get_resource().LoadFrame(None, name)


def get_child_control(parent, child):
    # We do this instead of XRCCTRL to work around a bug in wxPython 3.0.3.
    # FindWindowById, FindWindowByName and XRCCTRL all seem to return the
    # first-created "child" instead of the proper one; only FindWindow behaves
    # as expected.
    return parent.FindWindow(XRCID(child))


def get_menu_bar(name):
    return get_resource().LoadMenuBar(name)


def get_menu(name):
    return get_resource().LoadMenu(name)
