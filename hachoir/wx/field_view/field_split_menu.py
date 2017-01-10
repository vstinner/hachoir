import wx


class field_split_menu_t:
    def __init__(self, parent, menu):
        self.parent = parent
        self.menu = menu
        self.Bind = self.menu.Bind   # see note in field_menu.py

    def ask_split(self, caption, min, max):
        # Note: we would prefer a NumberEntryDialog but this isn't currently wrapped
        # by wxPython Phoenix.
        res = None
        dlg = wx.TextEntryDialog(self.parent, 'Enter split offset:', '',
                                 caption, min, min, max)
        if dlg.ShowModal() == wx.ID_OK:
            try:
                res = int(dlg.GetValue())
            except ValueError:
                res = None
        dlg.Destroy()
        return res
