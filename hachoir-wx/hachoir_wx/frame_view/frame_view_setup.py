# -*- coding: utf-8 -*-

from frame_view_imp import frame_view_imp_t
from frame_view_fwd import frame_view_fwd_t

from hachoir_wx.resource import get_frame

def setup_frame_view(dispatcher):
    print '[+] Setup frame view'
    frame = get_frame('frame_view')
    dispatcher.add_sender(frame)

    frame_view_imp = frame_view_imp_t()
    dispatcher.add(frame_view_imp)

    frame_view_fwd = frame_view_fwd_t(frame_view_imp)
    dispatcher.add_receiver(frame_view_fwd)

    return frame
