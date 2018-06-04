import wx


MAXITEMS = 1000


class FieldNodeData(object):
    def __init__(self, field):
        self.field = field
        self.child_map = {}
        self.enumerated = False
        self.seen = set()
        self.limit = MAXITEMS


class tree_view_t(wx.TreeCtrl):
    def __init__(self):
        wx.TreeCtrl.__init__(self)
        self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)

        self.filename = "/"
        self.root = None

    def post_init(self):
        self.root = self.AddRoot("/")
        self.setup_new_node(self.root, None)
        self.update_root_name()

        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpand)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivate)

        self.dispatcher.trigger('tree_view_ready', self)

    def OnCreate(self, event):
        self.Unbind(wx.EVT_WINDOW_CREATE)
        wx.CallAfter(self.post_init)

    def setup_new_node(self, node, field):
        self.AppendItem(node, "loading...")
        self.SetItemData(node, FieldNodeData(field))

    def enumerate_node(self, node, target=None, extend=0):
        data = self.GetItemData(node)
        if data.enumerated:
            return

        if target in data.seen:
            target = None

        n = len(data.seen)
        data.limit = max(n, data.limit + extend)
        if n == data.limit and not target:
            return

        # remove placeholder ("more..." or "loading...")
        self.Delete(self.GetLastChild(node))

        i = 0
        while 1:
            try:
                child = data.field[n + i]
            except Exception:
                # save memory
                data.limit = None
                data.seen = None
                data.enumerated = True
                return

            if child.is_field_set:
                childnode = self.AppendItem(node, child.name)
                data.child_map[child.name] = childnode
                self.setup_new_node(childnode, child)

            i += 1
            data.seen.add(child.name)
            if (not target or target == child.name) and len(data.seen) >= data.limit:
                self.AppendItem(node, "more...")
                break

    def find_node(self, field):
        path = field.path
        curnode = self.root
        segs = path.split('/')
        for i, seg in enumerate(segs):
            if seg:
                curnode = self.GetItemData(curnode).child_map[seg]

            if i < len(segs) - 1:
                nextseg = segs[i + 1]
            else:
                nextseg = None

            self.enumerate_node(curnode, nextseg)
        return curnode

    def update_root_name(self):
        if self.root is not None:
            self.SetItemText(self.root, self.filename)

    def OnExpand(self, event):
        self.enumerate_node(event.Item)

    def OnActivate(self, event):
        data = self.GetItemData(event.Item)
        if not data:
            # clicked on a "more..." item
            node = self.GetItemParent(event.Item)
            self.SetFocusedItem(self.GetPrevSibling(event.Item))
            self.enumerate_node(node, extend=MAXITEMS)
            self.SetFocusedItem(self.GetNextSibling(self.GetFocusedItem()))
            return
        self.dispatcher.trigger('field_activated', data.field)

    # --- dispatcher events ---
    def on_file_ready(self, dispatcher, file):
        assert file is not None
        self.filename = file.name
        self.update_root_name()

    def on_filename_update(self, dispatcher, filename):
        self.filename = filename
        self.update_root_name()

    def on_field_activated(self, dispatcher, field):
        self.cur_field = field
        self.GetItemData(self.root).field = field['/']
        node = self.find_node(field)
        self.Expand(node)
        self.SelectItem(node)
        self.ScrollTo(node)
