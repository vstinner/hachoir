import wx
from .file_cache import FileCache

try:
    import darkdetect
    darkmode = darkdetect.isDark()
except ImportError:
    darkmode = False


textchars = set('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ')
text_view_transtable = bytes([c if chr(c) in textchars else ord('.') for c in range(256)])


class HexViewLayout(object):
    ''' Encapsulates information about the layout of the address, hex and text panes. '''
    def __init__(self):
        self.winsize = (100, 100)
        self.charsize = (10, 10)
        self.addrchars = 2

        self.hborder = 2   # spacing between panes
        self.hpad = 4   # inner padding between pane edge and text

        self.dispatcher = None
        self.update()

    def set_winsize(self, winsize):
        if winsize != self.winsize:
            self.winsize = winsize
            self.update()

    def set_charsize(self, charsize):
        if charsize != self.charsize:
            self.charsize = charsize
            self.update()

    def set_addrchars(self, addrchars):
        if addrchars != self.addrchars:
            self.addrchars = addrchars
            self.update()

    @property
    def textrows(self):
        wh = self.winsize[1]
        ch = self.charsize[1]
        return (wh // ch) + 2

    @property
    def textcols(self):
        return self._textcols

    def update(self):
        w, h = self.winsize
        cw, ch = self.charsize
        mw = (self.hpad + self.hborder) * 2   # total margin width

        # calculate width of address pane
        addrpane_width = int((cw * self.addrchars) + mw)
        # +2 is a slight fudge to prevent tight layouts
        overhead = addrpane_width + mw * 2 + 2

        # figure out how many characters we can fit in the views
        # add one extra char to account for one less space in hexview
        availwidth = w - overhead + cw
        tc = max(int(availwidth / cw // 4), 1)

        # calculate the widths of the hex and text panes
        hexpane_width = int(cw * (tc * 3 - 1) + mw)
        textpane_width = int(cw * tc + mw)
        slack = w - addrpane_width - hexpane_width - textpane_width
        hexpane_width += slack // 2
        textpane_width += slack - slack // 2

        self.addrpane_width = addrpane_width
        self.hexpane_width = hexpane_width
        self.textpane_width = textpane_width
        self.addrpane_start = 0
        self.hexpane_start = self.addrpane_start + self.addrpane_width
        self.textpane_start = self.hexpane_start + self.hexpane_width

        self._textcols = tc

        if self.dispatcher:
            self.dispatcher.trigger('hex_view_layout_updated', self)

    def panestart(self, name):
        ''' Get the starting x position of the given pane, before border and margin '''
        return getattr(self, name + 'pane_start')

    def boxstart(self, name):
        ''' Get the starting x position of the given pane's textbox '''
        return getattr(self, name + 'pane_start') + self.hborder

    def boxwidth(self, name):
        ''' Get the width of the given pane's textbox '''
        return getattr(self, name + 'pane_width') - self.hborder * 2

    def textstart(self, name):
        ''' Get the starting x position of the text within the given pane '''
        return getattr(self, name + 'pane_start') + self.hpad + self.hborder


class hex_view_t(wx.ScrolledWindow):
    def __init__(self):
        wx.ScrolledWindow.__init__(self)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResized)
        self.Bind(wx.EVT_SCROLLWIN, self.OnScrolled)
        # OnCreate required to avoid crashing wx in xrc creation
        self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)

        # Disable physical scrolling - refresh entire display on each scroll event.
        self.EnableScrolling(False, False)
        # This line enables double-buffered painting for reduced flicker.
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        # The previous scroll action (for maintaining viewport during resizes).
        self.prev_scroll = None

        self.layout = HexViewLayout()

    def OnCreate(self, evt):
        pass

    def ready(self):
        self.layout.dispatcher = self.dispatcher
        self.layout.set_winsize(self.GetSize())
        self.dispatcher.trigger('hex_view_ready', self)

    def get_scroll_addr(self):
        ''' Return (addr, offset) where addr is the first address in the hex view
        and offset is the within-line pixel offset of the view. '''
        scrollpos = self.GetViewStart()[1]
        row, offset = divmod(scrollpos, self.layout.charsize[1])
        return row * self.layout.textcols, offset

    def highlight_region(self, dc, start, end):
        ''' Highlight the given range in the hex and text panes '''
        topleft, offset = self.get_scroll_addr()
        cw, ch = self.layout.charsize

        for row in range(self.layout.textrows):
            rowstart = topleft + row * self.layout.textcols
            rowend = rowstart + self.layout.textcols
            if rowend <= start or rowstart >= end:
                continue
            hl_start = max(start, rowstart)
            hl_end = min(end, rowend)

            hy = ch * row - offset
            hx = self.layout.textstart('hex') + (hl_start - rowstart) * 3 * cw
            hw = ((hl_end - hl_start) * 3 - 1) * cw
            hh = ch

            dc.DrawRectangle(hx, hy, hw, hh)

            hx = self.layout.textstart('text') + (hl_start - rowstart) * cw
            hw = (hl_end - hl_start) * cw
            dc.DrawRectangle(hx, hy, hw, hh)

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        lo = self.layout

        # Figure out how big characters are
        teststr = "A" * 16
        cw, ch = dc.GetTextExtent(teststr)
        cw /= float(len(teststr))
        lo.set_charsize((cw, ch))

        w, h = lo.winsize

        # Draw "textbox" rects under the hex and text views
        dc.SetPen(wx.NullPen)
        if darkmode:
            dc.SetBrush(wx.BLACK_BRUSH)
        else:
            dc.SetBrush(wx.WHITE_BRUSH)
        dc.DrawRectangle(lo.boxstart('hex'), 0, lo.boxwidth('hex'), h)
        dc.DrawRectangle(lo.boxstart('text'), 0, lo.boxwidth('text'), h)

        # Figure out where we are in the text
        start, offset = self.get_scroll_addr()

        # Draw highlights under the selected field
        if self.field_span is not None:
            dc.SetBrush(wx.LIGHT_GREY_BRUSH)
            self.highlight_region(dc, *self.field_span)

        # Draw the actual text
        size = lo.textcols * lo.textrows
        text = self.fcache.get(start, start + size)
        cury = -offset
        for i in range(0, size, lo.textcols):
            dc.DrawText(self.format_address(start + i), lo.textstart('addr'), cury)
            dc.DrawText(" ".join("%02x" % c for c in text[i:i + lo.textcols]), lo.textstart('hex'), cury)
            dc.DrawText(text[i:i + lo.textcols].translate(text_view_transtable), lo.textstart('text'), cury)
            cury += ch

    def OnResized(self, event):
        self.layout.set_winsize(self.GetClientSize())

        if self.prev_scroll is not None:
            op, args = self.prev_scroll
            if op == 'jump':
                self.scroll_to(*args)
            elif op == 'scroll':
                # Scroll to keep the previous top-left byte visible
                addr, offset = args
                target_row = addr // self.layout.textcols
                self.Scroll(0, target_row * self.layout.charsize[1] + offset)

        self.Refresh()

    def set_prev_scroll(self):
        self.prev_scroll = ('scroll', self.get_scroll_addr())

    def OnScrolled(self, event):
        wx.CallAfter(self.set_prev_scroll)
        # ensure that the scroll event is normally handled
        event.Skip()

    def scroll_to(self, start, end):
        ''' Scroll view so that [start,end) is in view.

        If the entire range can't be shown at once, it will scroll
        to show as much of the start of the range as possible.

        This method will attempt to scroll by the minimum distance
        necessary to get there. '''

        tc = self.layout.textcols
        tr = self.layout.textrows
        cw, ch = self.layout.charsize

        startrow = start // tc
        endrow = (end + tc - 1) // tc

        # scroll so that [startrow, endrow) is in view
        if endrow - startrow >= tr - 2:
            # range occupies the entire view or more: scroll there directly
            self.Scroll(0, startrow * ch)
            return

        # Two choices: scroll so the selection touches the top, or so the selection touches the bottom
        s1 = startrow * ch
        s2 = (endrow - (tr - 2)) * ch

        cur = self.GetViewStart()[1]
        if s2 <= cur <= s1:
            # no need to scroll: the item is already visible in the view
            return
        elif s2 <= s1 <= cur:
            # scroll backwards
            self.Scroll(0, s1)
        else:
            # scroll forwards
            self.Scroll(0, s2)

    def update_address_width(self):
        maxaddr = self.fcache.filesize - 1
        if self.hexaddr:
            addrchars = max(len('%x' % maxaddr), 2)
        else:
            addrchars = max(len('%d' % maxaddr), 2)
        self.layout.set_addrchars(addrchars)

    def format_address(self, addr):
        if self.hexaddr:
            return ('%x' % addr).zfill(self.layout.addrchars)
        else:
            return ('%d' % addr).rjust(self.layout.addrchars)

    # ---------- dispatcher events ----------

    def on_file_ready(self, dispatcher, file):
        assert file is not None
        self.fcache = FileCache(file)

        self.field = None
        self.field_span = None
        self.hexaddr = True
        self.update_address_width()
        self.Refresh()

    def on_address_decimal(self, dispatcher):
        self.hexaddr = False
        self.update_address_width()
        self.Refresh()

    def on_address_hexadecimal(self, dispatcher):
        self.hexaddr = True
        self.update_address_width()
        self.Refresh()

    def on_hex_view_layout_updated(self, dispatcher, layout):
        # Update scrollbar sizes
        textcols = layout.textcols
        totalrows = (self.fcache.filesize + textcols - 1) // textcols
        winheight = layout.winsize[1]
        totalheight = max(totalrows * layout.charsize[1], winheight)
        width = layout.winsize[0]

        self.SetScrollbars(0, 1, 0, winheight)
        self.SetVirtualSize((width, totalheight))

        # Refresh view
        self.Refresh()

    def on_field_selected(self, dispatcher, field):
        self.field = field
        self.field_span = field.absolute_address // 8, (field.absolute_address + field.size + 7) // 8
        self.scroll_to(*self.field_span)
        self.prev_scroll = ('jump', self.field_span)
        self.Refresh()
