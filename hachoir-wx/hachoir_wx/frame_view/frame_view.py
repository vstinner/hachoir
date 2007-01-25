# -*- coding: utf-8 -*-

from wx import Frame, PreFrame

class frame_view_t(Frame):
    def __init__(self):
        pre = PreFrame()
        self.PostCreate(pre)

    def ready(self):
        self.dispatcher.trigger('frame_view_ready', self)

