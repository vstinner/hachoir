# -*- coding: utf-8 -*-

# Windows wx compatibility

def get_width_chars(view):
    return ((view.GetClientSize()[0]-3) // (view.GetCharWidth()-1) - 1) // 3

def get_height_chars(view):
    return view.GetClientSize()[1] // view.GetCharHeight()
