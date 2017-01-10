# platform workarounds
import wx
if '__WXGTK__' == wx.Platform:
    from .compat_gtk import get_width_chars, get_height_chars   # noqa
elif '__WXMSW__' == wx.Platform:
    from .compat_msw import get_width_chars, get_height_chars   # noqa
else:
    from .compat_all import get_width_chars, get_height_chars   # noqa

from .hex_view import hex_view_t   # noqa
from .hex_view_scroll import hex_view_scroll_t   # noqa
from .hex_view_setup import setup_hex_view   # noqa
