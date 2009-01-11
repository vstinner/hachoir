# -*- coding: utf-8 -*-

MAX_LINE_TEST = 10 * 1024

def get_width_chars(view):
    if not view.GetLineLength(0):
        padding = ' ' * MAX_LINE_TEST
        view.SetValue(padding)

    return view.GetLineLength(0) // 3
    
def get_height_chars(view):
    return view.GetClientSize()[1] // view.GetCharHeight()

