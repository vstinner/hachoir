# -*- coding: utf-8 -*-

class frame_view_imp_t:
    def on_frame_view_ready(self, dispatcher, frame_view):
        assert frame_view is not None
        self.view = frame_view

    def on_file_ready(self, dispatcher, file):
        assert file is not None
        self.filename = file.name

    def on_filename_update(self, dispatcher, filename):
        self.filename = filename

    def format_title(self, field):
        field_path = field._getPath()
        return self.filename+'/'+field_path[1:]

    def on_field_activated(self, dispatcher, field):
        self.view.SetTitle(self.format_title(field))

    def on_activated(self):
        self.dispatcher.trigger('frame_activated', self.view)
