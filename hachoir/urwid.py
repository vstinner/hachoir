from hachoir.core.i18n import getTerminalCharset
from hachoir.core.tools import humanFilesize, humanBitSize, makePrintable
from hachoir.core.log import log as hachoir_log
from hachoir.core.cmd_line import getHachoirOptions, configureHachoir
from hachoir.core.cmd_line import displayVersion

from hachoir.field import Field, MissingField
from hachoir.stream import InputFieldStream, InputStreamError, FileInputStream
from hachoir.parser import guessParser, HachoirParserList
from urwid import (AttrWrap, BoxAdapter, CanvasJoin, Edit, Frame, ListBox,
                   Pile, Text, WidgetPlaceholder)
from shutil import copyfileobj
from weakref import WeakKeyDictionary
from optparse import OptionGroup, OptionParser
import os
import sys
import urwid.curses_display

try:
    from urwid import __version__ as urwid_ver
except ImportError:
    urwid_ver = None
try:
    from urwid import ListWalker
except ImportError:
    class ListWalker(object):

        def _modified(self):
            pass


def browse_completion(text):
    path = os.path.dirname(text)
    for name in os.listdir(path):
        name = os.path.join(path, name)
        if os.path.isdir(name):
            name += os.sep
        yield name


class NewTab_Stream(Exception):

    def __init__(self, field):
        self.field = field


class NeedInput(Exception):

    def __init__(self, *args):
        self.args = args


class TextField(AttrWrap):
    start = 0

    def __init__(self, text):
        AttrWrap.__init__(self, Text(text, wrap='clip'), None, 'focus')

    def selectable(self):
        return True

    def keypress(self, arg, key):
        return key


class Node:

    def __init__(self, field, parent=None):
        self.parent = parent
        self.childs = []
        self.flags = None
        if parent:
            self.depth = parent.depth + 1
            self.index = field
            self.field = parent.field[self.index]
            if self.field.is_field_set:
                self.text = ' +'
            else:
                self.text = '  '
            self.text = '   ' * parent.depth + self.text + ' (...)'
        else:
            self.depth = 0
            self.index = None
            self.field = field
            self.text = ''
        self.widget = TextField(self.text)

    def setText(self, text, flags):
        self.text = text
        self.flags = flags
        self.widget.start = None

    def getWidget(self, start):
        if start != self.widget.start:
            self.widget.start = start
            self.widget.set_text(self.text[start:])
        return self.widget

    def hidden(self):
        parent = self.parent
        return (parent and parent.childs[-1] == self
                and (len(parent.childs) < parent.field.current_length
                     or not parent.field.done))

    def sync(self):
        start, end = len(self.childs), self.field.current_length
        if start < end:
            self.childs += [Node(i, self) for i in range(start, end)]

    def refresh(self):
        if self.flags:
            self.flags = 0
        if self.childs:
            for index, child in enumerate(self.childs):
                if (index >= self.field.current_length
                        or child.field != self.field[index]):
                    del self.childs[index:]
                    break
                child.refresh()
            self.sync()


class Walker(ListWalker):
    valid = 1 << 0
    display_value = 1 << 1
    display_size = 1 << 2
    human_size = 1 << 3
    use_absolute_address = 1 << 4
    hex_address = 1 << 5
    display_description = 1 << 6
    display_type = 1 << 7
    flags = valid
    start = 0
    event = False

    def __init__(self, charset, root, preload_fields, focus, options):
        self.charset = charset
        if options.get("display_value", True):
            self.flags |= self.display_value
        if options.get("description", True):
            self.flags |= self.display_description
        if options.get("display_type", False):
            self.flags |= self.display_type
        if options.get("display_size", True):
            self.flags |= self.display_size
        if options.get("human-size", True):
            self.flags |= self.human_size
        if options.get("absolute-address", False):
            self.flags |= self.use_absolute_address
        if options.get("hex-address", False):
            self.flags |= self.hex_address
        assert preload_fields > 0
        self.preload_fields = preload_fields
        self.focus = root
        for event in ("field-value-changed", "field-resized", "field-inserted", "field-replaced", "set-field-value"):
            root.field.connectEvent(event, self.onEvent, False)
        self.keypress(None, 'enter')
        if focus:
            self.set_focus(self.fromField(root, focus))

    def onEvent(self, event, *args):
        self.event = True

    def getRoot(self):
        pos = self.focus
        while pos.parent:
            pos = pos.parent
        return pos

    def fromField(self, root, path):
        try:
            field = self.focus.field[path]
        except MissingField as e:
            field = e.field
            hachoir_log.error(str(e))
        path = []
        while field.parent:
            path.append(field.index)
            field = field.parent
        for index in reversed(path):
            self.read(root, index + 2, True)
            root = root.childs[index]
        return root

    def sync(self):
        if self.event:
            self.event = False
            path = self.focus.field.path
            root = self.getRoot()
            root.refresh()
            self.set_focus(self.fromField(root, path))
            assert not self.event

    def read(self, pos, number, first=False):
        if first:
            number = number - pos.field.current_length
        pos.field.readMoreFields(number)
        pos.sync()
        self.sync()

    def keypress(self, size, key):
        if key == 'right':
            self.start += 1
        elif key == 'left':
            if not self.start:
                return
            self.start -= 1
        elif key == 'a':
            self.flags ^= self.use_absolute_address
        elif key == 'b':
            self.flags ^= self.hex_address
        elif key == 'h':
            self.flags ^= self.human_size
        elif key == 's':
            self.flags ^= self.display_size
        elif key == 't':
            self.flags ^= self.display_type
        elif key == 'v':
            self.flags ^= self.display_value
        elif key == 'd':
            self.flags ^= self.display_description
        elif key in ('ctrl e', 'ctrl x'):
            if self.focus.field.size != 0:
                raise NeedInput(lambda path: self.save_field(path, key == 'ctrl e'),
                                'save field to: ', os.getcwd() + os.sep, browse_completion)
            return
        elif key == 'enter':
            pos = self.focus
            if pos.field.is_field_set:
                pos.flags = 0
                if pos.childs:
                    pos.childs = []
                else:
                    self.read(pos, self.preload_fields, True)
            elif pos.field.size == 0:
                root = self.getRoot()
                target = pos.field.value
                if self.event:
                    self.event = False
                    root.refresh()
                    assert not self.event
                if target:
                    self.set_focus(self.fromField(root, target.path))
                return
        elif key == ' ':
            if 0 < self.focus.field.size < self.getRoot().field.stream.size:
                raise NewTab_Stream(self.focus.field)
            return
        else:
            return key
        self._modified()

    def update(self, node):
        if node.depth:
            text = ' ' * (3 * node.depth - 2)
            if node.childs:
                text += '- '
            elif node.field.is_field_set:
                text += '+ '
            else:
                text += '  '
            name = node.field.name
        else:
            text = ''
            name = node.field.stream.source

        if node.field.size:
            if self.flags & self.use_absolute_address:
                address = node.field.absolute_address
            else:
                address = node.field.address
            display_bits = (address % 8) != 0 or (node.field.size % 8) != 0

            if self.flags & self.hex_address:
                if display_bits:
                    text += "%04x.%x" % (address // 8, address % 8)
                else:
                    text += "%04x" % (address // 8)
            else:
                if display_bits:
                    text += "%u.%u" % (address // 8, address % 8)
                else:
                    text += "%u" % (address // 8)
            text += ") " + name
        else:
            text += "-> " + name

        smart_display = True
        if self.flags & self.display_value and node.field.hasValue():
            if self.flags & self.human_size:
                display = node.field.display
            else:
                display = node.field.raw_display
                smart_display = False
            text += "= %s" % display
        if node.field.description and self.flags & self.display_description:
            description = node.field.description
            if not(self.flags & self.human_size):
                description = makePrintable(description, "ASCII")
            text += ": %s" % description
        if self.flags & self.display_size and node.field.size or self.flags & self.display_type:
            tmp_text = []
            if self.flags & self.display_type:
                tmp_text.append(node.field.getFieldType())
            if self.flags & self.display_size:
                if node.field.size % 8:
                    tmp_text.append(humanBitSize(node.field.size))
                else:
                    size = node.field.size // 8
                    if not self.flags & self.human_size:
                        tmp_text.append("%u bytes" % size)
                    else:
                        tmp_text.append(humanFilesize(size))
            text += " (%s)" % ", ".join(tmp_text)
        text = makePrintable(text, self.charset, smart=smart_display)
        node.setText(text, self.flags)

    def _get(self, pos):
        if not pos:
            return None, None
        if pos.parent and pos.field != pos.parent.field[pos.index]:
            hachoir_log.error("assertion failed at urwid_ui.Walker._get")
        if not (pos.flags is None and pos.hidden()) and pos.flags != self.flags:
            self.update(pos)
        return pos.getWidget(self.start), pos

    def get_focus(self):
        return self._get(self.focus)

    def get_next(self, pos):
        if pos.childs:
            return self._get(pos.childs[0])
        while pos.parent:
            next = pos.index + 1
            pos = pos.parent
            if next < len(pos.childs):
                return self._get(pos.childs[next])
        return None, None

    def get_prev(self, pos):
        if pos.index:
            pos = pos.parent.childs[pos.index - 1]
            while pos.childs:
                pos = pos.childs[-1]
        else:
            pos = pos.parent
        return self._get(pos)

    def set_focus(self, pos):
        self.focus = pos
        if pos.flags is None and pos.parent:
            self.read(pos.parent, self.preload_fields)
        self._modified()

    def get_home(self):
        if self.focus.parent:
            return self.focus.parent

    def get_end(self):
        pos = self.focus
        if pos.childs:
            pos = pos.childs[-1]
        elif not pos.parent:
            return
        else:
            while pos == pos.parent.childs[-1]:
                pos = pos.parent
                if not pos.parent:
                    return
            pos = pos.parent.childs[-1]
#            if pos.flags is None and pos.hidden():
#                next = self.get_next(pos)[1]
#                if next:
#                    pos = next
        return pos

    def save_field(self, path, raw):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError as err:
            hachoir_log.error(str(err))
        else:
            field = self.focus.field
            if raw:
                stream = InputFieldStream(field)
            else:
                stream = field.getSubIStream()
            copyfileobj(stream.file(), os.fdopen(fd, 'wb'))


class TreeBox(ListBox):

    def __init__(self, charset, root, preload_fields, focus, options={}):
        ListBox.__init__(self, Walker(
            charset, root, preload_fields, focus, options))

    def keypress(self, size, key):
        key = self.body.keypress(size, key)
        if key == 'home':
            pos = self.body.get_home()
            if pos:
                self.change_focus(size, pos, coming_from='below')
        elif key == 'end':
            pos = self.body.get_end()
            if pos:
                self.change_focus(size, pos, coming_from='above')
        elif key:
            return ListBox.keypress(self, size, key)

    def render(self, size, focus=False):
        self.body.sync()
        canvas = ListBox.render(self, size, focus)
        if self.body.event:
            self.body.sync()
            canvas = ListBox.render(self, size, focus)
            assert not self.body.event
        return canvas


class Tabbed(WidgetPlaceholder):
    tabs = []
    active = None

    def __init__(self, title):
        WidgetPlaceholder.__init__(self, None)
        self.title = title

    def select(self, pos):
        self.active = pos
        if pos is None:
            self.original_widget = None
        else:
            self.original_widget = self.tabs[pos][1]
        tabs = []
        for i, t in enumerate(self.tabs):
            tab = " %u %s " % (i, t[0])
            if i == pos:
                tab = ('focus', tab)
            tabs.append(tab)
        self.title.set_text(tabs if tabs else '')

    def append(self, tab):
        pos = len(self.tabs)
        self.tabs.append(tab)
        self.select(pos)

    def close(self):
        pos = self.active
        del self.tabs[pos]
        if pos == len(self.tabs):
            if pos:
                pos -= 1
            else:
                pos = None
        self.select(pos)

    def keypress(self, size, key):
        if key == '<':
            pos = self.active - 1
        elif key == '>':
            pos = self.active + 1
        else:
            return self.original_widget.keypress(size, key)
        self.select(pos % len(self.tabs))


class Separator(Text):

    def __init__(self, format):
        Text.__init__(self, '')
        self.format = format
        self.info = Text('')

    def set_info(self, *args):
        self.info.set_text(self.format % args)

    def cols(self, maxcol):
        lines = len(self.get_text()[0])
        r = len(self.info.get_text()[0])
        lr = lines + r
        mc = maxcol - 2
        if lr <= mc:
            return lines, r
        return lines * mc // lr, r * mc // lr

    if urwid_ver < '0.9.8':
        def render(self, xxx_todo_changeme, focus=False):
            (maxcol,) = xxx_todo_changeme
            lines, r = self.cols(maxcol)
            return CanvasJoin([
                Text.render(self, (lines,), focus),
                maxcol - r, self.info.render((r,)),
            ])
    else:
        def render(self, xxx_todo_changeme1, focus=False):
            (maxcol,) = xxx_todo_changeme1
            lines, r = self.cols(maxcol)
            return CanvasJoin([
                (Text.render(self, (lines,), focus), None, True, maxcol - r),
                (self.info.render((r,)), None, False, r),
            ])

    def rows(self, xxx_todo_changeme3, focus=False):
        (maxcol,) = xxx_todo_changeme3
        lines, r = self.cols(maxcol)
        return max(Text.rows(self, (lines,), focus), self.info.rows((r,)))


class Input(Edit):
    _end = False

    def __init__(self, enter, leave):
        self._top = enter, leave
        Edit.__init__(self)

    def do(self, done, caption='', text='', tab=None):
        self._done = done
        self._tab = tab
        self.set_caption(caption)
        self.set_edit_text(text)
        self._end = True  # TODO: find a better way to move the cursor the end.
        self._top[0](AttrWrap(self, 'input'))

    def move_cursor_to_coords(self, size, x, y):
        if self._end:
            x = "right"
            self._end = False
        return Edit.move_cursor_to_coords(self, size, x, y)

    def keypress(self, size, key):
        if key == 'enter':
            self._top[1]()
            self._done(self.get_edit_text())
        elif key == 'esc':
            self._top[1]()
        elif key == 'tab' and self._tab:
            text = self.get_edit_text()[:self.edit_pos]
            text_len = len(text)
            match = None
            for entry in self._tab(text):
                if entry.startswith(text):
                    entry = entry[text_len:]
                    if match is None:
                        match = entry
                    else:
                        while not entry.startswith(match):
                            match = match[:-1]
            if match:
                self.insert_text(match)
        else:
            return Edit.keypress(self, size, key)


def getHelpMessage():
    actions = ("Application:",
               ("q", "exit"),
               ("F1", "help"),
               ("< / >", "prev/next tab"),
               ("+ / -", "move separator vertically"),
               ("esc/^W", "close current tab"),
               ), ("Parser window:",
                   ("a", "absolute address"),
                   ("b", "address in hexadecimal"),
                   ("h", "human display"),
                   ("d", "description"),
                   ("s", "field set size"),
                   ("t", "field type"),
                   ("v", "field value"),
                   ("^E", "save field to a file"),
                   ("^X", "create a stream from the selected field and save it to a file"),
                   ("enter", "collapse/expand"),
                   ("(page) up/down", "move (1 page) up/down"),
                   ("home", "move to parent field"),
                   ("end", "move to last (parent) field"),
                   ("<-/->", "scroll horizontally"),
                   ("space", "parse the selected field"),
                   )
    length = 4 + max(max(len(action[0])
                         for action in group[1:]) for group in actions)
    return "\n".join("\n    %s\n%s" % (group[0],
                                       "\n".join("%*s   %s" % (length, action[0], action[1])
                                                 for action in group[1:])) for group in actions)


def exploreFieldSet(field_set, args, options={}):
    charset = getTerminalCharset()

    ui = urwid.curses_display.Screen()
    ui.register_palette((
        ('focus', 'white', 'dark blue'),
        ('sep', 'white', 'dark red'),
        ('input', 'black', 'light gray'),
    ))

    msgs = [[], [], 0]
    hachoir_log.use_print = False

    def logger(level, prefix, text, ctxt):
        if ctxt is not None:
            c = []
            if hasattr(ctxt, "_logger"):
                c[:0] = [ctxt._logger()]
            if issubclass(ctxt.__class__, Field):
                ctxt = ctxt["/"]
            name = logger.objects.get(ctxt)
            if name:
                c[:0] = [name]
            if c:
                text = "[%s] %s" % ('|'.join(c), text)
        if not isinstance(text, str):
            text = str(text, charset)
        msgs[0].append((level, prefix, text))
    logger.objects = WeakKeyDictionary()
    hachoir_log.on_new_message = logger

    preload_fields = 1 + max(0, args.preload)

    log_count = [0, 0, 0]
    sep = Separator("log: %%u/%%u/%%u  |  %s  " % "F1: help")
    sep.set_info(*tuple(log_count))
    body = Tabbed(sep)
    help = ('help', ListBox([Text(getHelpMessage())]))
    logger.objects[field_set] = logger.objects[
        field_set.stream] = name = 'root'
    body.append((name, TreeBox(charset, Node(field_set, None),
                               preload_fields, args.path, options)))

    log = BoxAdapter(ListBox(msgs[1]), 0)
    log.selectable = lambda: False
    wrapped_sep = AttrWrap(sep, 'sep')
    footer = Pile([('flow', wrapped_sep), log])

    # awful way to allow the user to hide the log widget
    log.render = lambda size, focus=False: BoxAdapter.render(log, size[
                                                             :1], focus)
    footer.render = lambda arg, focus=False: Pile.render(
        footer, (arg[0], sep.rows(arg) + log.height), focus)

    top = Frame(body, None, footer)

    def input_enter(w):
        footer.widget_list[0] = w
        footer.set_focus(0)
        top.set_focus('footer')

    def input_leave():
        footer.widget_list[0] = wrapped_sep
        footer.set_focus(0)
        top.set_focus('body')
    input = Input(input_enter, input_leave)

    def run():
        msg = _resize = retry = 0
        events = ("window resize", )
        profile_display = args.profile_display
        while True:
            for e in events:
                try:
                    if e == "window resize":
                        size = ui.get_cols_rows()
                        resize = log.height
                    else:
                        e = top.keypress(size, e)
                        if e is None:
                            pass
                        elif e in ('f1', '?'):
                            try:
                                body.select(body.tabs.index(help))
                            except ValueError:
                                body.append(help)
                                resize = log.height
                        elif e in ('esc', 'ctrl w'):
                            body.close()
                            if body.original_widget is None:
                                return
                            resize = log.height
                        elif e == '+':
                            if log.height:
                                resize = log.height - 1
                        elif e == '-':
                            resize = log.height + 1
                        elif e == 'q':
                            return
                # except AssertionError:
                #     hachoir_log.error(getBacktrace())
                except NewTab_Stream as e:
                    stream = e.field.getSubIStream()
                    logger.objects[
                        stream] = e = "%u/%s" % (body.active, e.field.absolute_address)
                    parser = guessParser(stream)
                    if not parser:
                        hachoir_log.error(
                            "No parser found for %s" % stream.source)
                    else:
                        logger.objects[parser] = e
                        body.append(
                            (e, TreeBox(charset, Node(parser, None), preload_fields, None, options)))
                        resize = log.height
                except NeedInput as e:
                    input.do(*e.args)
                if profile_display:
                    events = events[1:]
                    break
            while True:
                if msgs[0]:
                    for level, prefix, text in msgs[0]:
                        log_count[level] += 1
                        txt = Text("[%u]%s %s" % (msg, prefix, text))
                        msg += 1
                        msgs[1].append(txt)
                        _resize += txt.rows(size[:1])
                    if log.height < _resize and (resize is None or resize < _resize):
                        resize = _resize
                    try:
                        log.set_focus(len(msgs[1]) - 1)
                    except IndexError:
                        pass
                    sep.set_info(*tuple(log_count))
                    msgs[0] = []
                if resize is not None:
                    body.height = size[1] - sep.rows(size[:1]) - resize
                    if body.height <= 0:
                        resize += body.height - 1
                        body.height = 1
                    log.height = resize
                    resize = None
                canvas = top.render(size, focus=True)
                if not msgs[0]:
                    _resize = retry = 0
                    break
                assert not retry
                retry += 1
            ui.draw_screen(size, canvas)
            msgs[2] = len(msgs[1])
            if profile_display and events:
                continue
            while True:
                events = ui.get_input()
                if events:
                    break

    try:
        ui.run_wrapper(run)
    except Exception:
        pending = [msg.get_text()[0] for msg in msgs[1][msgs[2]:]] + \
                  ["[*]%s %s" % (prefix, text)
                   for level, prefix, text in msgs[0]]
        if pending:
            print("\nPending messages:\n" + '\n'.join(pending))
        raise


def displayParserList(*args):
    HachoirParserList().print_()
    sys.exit(0)


def parseOptions():
    parser = OptionParser(usage="%prog [options] filename")

    common = OptionGroup(parser, "Urwid", "Option of urwid explorer")
    common.add_option("--preload", help="Number of fields to preload at each read",
                      type="int", action="store", default=15)
    common.add_option("--path", help="Initial path to focus on",
                      type="str", action="store", default=None)
    common.add_option("--parser", help="Use the specified parser (use its identifier)",
                      type="str", action="store", default=None)
    common.add_option("--offset", help="Skip first bytes of input file",
                      type="long", action="store", default=0)
    common.add_option("--parser-list", help="List all parsers then exit",
                      action="callback", callback=displayParserList)
    common.add_option("--profiler", help="Run profiler",
                      action="store_true", default=False)
    common.add_option("--profile-display", help="Force update of the screen beetween each event",
                      action="store_true", default=False)
    common.add_option("--size", help="Maximum size of bytes of input file",
                      type="long", action="store", default=None)
    common.add_option("--hide-value", dest="display_value", help="Don't display value",
                      action="store_false", default=True)
    common.add_option("--hide-size", dest="display_size", help="Don't display size",
                      action="store_false", default=True)
    common.add_option("--version", help="Display version and exit",
                      action="callback", callback=displayVersion)
    parser.add_option_group(common)

    hachoir = getHachoirOptions(parser)
    parser.add_option_group(hachoir)

    values, arguments = parser.parse_args()
    if len(arguments) != 1:
        parser.print_help()
        sys.exit(1)
    return values, arguments[0]


def profile(func, *args):
    from hachoir.core.profiler import runProfiler
    runProfiler(func, args)


def openParser(parser_id, filename, offset, size):
    tags = []
    if parser_id:
        tags += [("id", parser_id), None]
    try:
        stream = FileInputStream(filename,
                                 offset=offset, size=size, tags=tags)
    except InputStreamError as err:
        return None, "Unable to open file: %s" % err
    parser = guessParser(stream)
    if not parser:
        return None, "Unable to parse file: %s" % filename
    return parser, None


def main():
    # Parser options and initialize Hachoir
    values, filename = parseOptions()
    configureHachoir(values)

    # Open file and create parser
    parser, err = openParser(values.parser, filename,
                             values.offset, values.size)
    if err:
        print(err)
        sys.exit(1)

    # Explore file
    with parser:
        if values.profiler:
            profile(exploreFieldSet, parser, values)
        else:
            exploreFieldSet(parser, values, {
                "display_size": values.display_size,
                "display_value": values.display_value,
            })


if __name__ == "__main__":
    main()
