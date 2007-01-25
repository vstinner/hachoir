# -*- coding: utf-8 -*-

from wx import ListCtrl, PreListCtrl, EVT_WINDOW_CREATE, CallAfter
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
from sys import maxint
from hachoir_core.i18n import _

class field_view_t(ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self):
        self.cols = {}

        pre = PreListCtrl()
        self.PostCreate(pre)
        self.Bind(EVT_WINDOW_CREATE, self.on_create)

    def post_init(self):
        ListCtrlAutoWidthMixin.__init__(self)

        columns = [_('address'), _('name'), _('type'), _('size'), _('data')]
        for name in columns:
            self.append_column(name)

        self.Layout()
        self.Fit()
        self.dispatcher.trigger('field_view_ready', self)

    def on_create(self, event):
        self.Unbind(EVT_WINDOW_CREATE)
        CallAfter(self.post_init)

    def append_column(self, name):
        index = self.GetColumnCount()
        self.cols[name] = index
        self.InsertColumn(col = index, heading = name)

    def append_row(self, col_map):
        index = self.InsertStringItem(maxint, '')
        for name, value in col_map.iteritems():
            col_index = self.cols[name]
            self.SetStringItem(index, col_index, value)
            self.autosize_column(col_index, value)

    def get_selected(self, name):
        return self.GetItem(self.GetFocusedItem(), self.cols[_('name')]).GetText()

    def clear(self):
        self.DeleteAllItems()

    def autosize_column(self, col_index, value):
        item_width = self.GetCharWidth() * (len(value) + 1)
        self.SetColumnWidth(col_index, max(item_width, self.GetColumnWidth(col_index)))
