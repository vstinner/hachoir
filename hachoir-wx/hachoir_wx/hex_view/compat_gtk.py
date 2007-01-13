# -*- coding: utf-8 -*-

# compatibility routines to work around bugs in wxgtk
def get_width_chars(view):
    return (view.GetClientSize()[0] - 4) // view.GetCharWidth() // 3

def get_height_chars(view):
    return (view.GetClientSize()[1] - 4) // view.GetCharHeight()

