from wx import Frame, EVT_WINDOW_CREATE


class frame_view_t(Frame):

    def __init__(self):
        Frame.__init__(self)
        # OnCreate required to avoid crashing wx
        self.Bind(EVT_WINDOW_CREATE, self.OnCreate)

    def OnCreate(self, evt):
        pass

    def ready(self):
        self.dispatcher.trigger('frame_view_ready', self)
