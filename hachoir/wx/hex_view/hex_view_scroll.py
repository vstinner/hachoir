from wx import ScrollBar, EVT_WINDOW_CREATE


class hex_view_scroll_t(ScrollBar):

    def __init__(self):
        ScrollBar.__init__(self)
        # OnCreate required to avoid crashing wx
        self.Bind(EVT_WINDOW_CREATE, self.OnCreate)

    def OnCreate(self, evt):
        pass

    def ready(self):
        self.dispatcher.trigger('hex_view_scroll_ready', self)
