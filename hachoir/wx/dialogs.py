import wx
import os


def file_open_dialog():
    dialog_style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST

    dialog = wx.FileDialog(
        None, message='Open',
        defaultDir=os.getcwd(),
        defaultFile='', style=dialog_style)

    return dialog


def file_save_dialog(title):
    dialog_style = wx.FD_SAVE

    dialog = wx.FileDialog(
        None, message=title,
        defaultDir=os.getcwd(),
        defaultFile='', style=dialog_style)

    return dialog
