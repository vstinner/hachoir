import wx
import os
from hachoir.core.i18n import _


def file_open_dialog():
    dialog_style = wx.OPEN | wx.FILE_MUST_EXIST

    dialog = wx.FileDialog(
        None, message=_('Open'),
        defaultDir=os.getcwd(),
        defaultFile='', style=dialog_style)

    return dialog


def file_save_dialog(title):
    dialog_style = wx.SAVE

    dialog = wx.FileDialog(
        None, message=title,
        defaultDir=os.getcwd(),
        defaultFile='', style=dialog_style)

    return dialog
