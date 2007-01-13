# -*- coding: utf-8 -*-

from hachoir_core.field import available_types
from hachoir_wx.field_view.mutator import convert_field
from hachoir_wx.field_view.stubs import can_convert

class core_type_menu_imp_t:
    def __init__(self):
        self.cur_field = None

    def on_core_type_menu_ready(self, dispatcher, view):
        assert view is not None
        self.view = view

    def on_type_selected(self, id):
        convert_field(self.cur_field, self.view.get_type_name(id))
        self.dispatcher.trigger('field_modified', self.cur_field)

    def on_field_selected(self, dispatcher, field):
        self.cur_field = field
        
        self.view.clear()
        for type in available_types:
            if can_convert(field, type) and field.__class__ is not type:
                self.view.add_type(type.__name__)
