import wx


class frame_view_t(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self)
        # OnCreate required to avoid crashing wx
        self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)

    def OnCreate(self, evt):
        pass

    def ready(self):
        self.dispatcher.trigger('frame_view_ready', self)
