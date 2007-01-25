# -*- coding: utf-8 -*-

from wx import App
from wx.xrc import XRCID

from hachoir_parser.guess import createParser
from hachoir_wx.dispatcher import dispatcher_t
from hachoir_wx import frame_view, field_view, hex_view
from hachoir_wx.dialogs import file_open_dialog
from hachoir_wx.unicode import force_unicode
from hachoir_wx import __version__ as VERSION

class app_t(App):
    def __init__(self, filename=None, real_filename=None):
        print "[+] Run hachoir-wx version %s" % VERSION
        if filename:
            self.init_filename = (filename, real_filename)
        else:
            self.init_filename = None
        App.__init__(self, False)

    def OnInit(self):
        self.bind_events()
        if self.init_filename:
            self.load_file(*self.init_filename)
        else:
            self.on_file_menu_open_file(None)
        return True

    def bind_events(self):
        self.Bind(wx.EVT_MENU, self.on_file_menu_open_file,
                  id=XRCID('file_menu_open_file'))
        self.Bind(wx.EVT_MENU, self.on_file_menu_close_window,
                  id=XRCID('file_menu_close_window'))

    def load_file(self, filename, realname):
        print '[+] Load file "%s"' % filename
        parser = createParser(filename, real_filename=realname)
        if parser:
            dispatcher = dispatcher_t()
            dispatcher.add_receiver(self)

            frame = frame_view.setup_frame_view(dispatcher)
            field_view.setup_field_view(frame, dispatcher)
            hex_view_widget = hex_view.setup_hex_view(frame, dispatcher)

            dispatcher.trigger('file_ready', open(realname, 'rb'))
            dispatcher.trigger('field_set_ready', parser)
            frame.ready()
            hex_view_widget.ready()

            frame.Show()
            print '[+] GUI ready'

    def on_file_menu_open_file(self, event):
        open_dialog = file_open_dialog()
        if wx.ID_OK == open_dialog.ShowModal():
            filename = open_dialog.GetPath()
            filename, realname = force_unicode(filename), filename
            open_dialog.Destroy()
            self.load_file(filename, realname)

    def on_frame_activated(self, dispatcher, frame):
        self.SetTopWindow(frame)

    def on_file_menu_close_window(self, event):
        top_window = self.GetTopWindow()
        assert top_window is not None
        top_window.Close()
