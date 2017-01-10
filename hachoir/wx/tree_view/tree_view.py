import wx


class FieldNodeData(object):
    def __init__(self, field):
        self.field = field
        self.enumerated = False
        self.child_map = {}


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

    def enumerate_node(self, node, field):
        self.DeleteChildren(node)
        data = self.GetItemData(node)
        data.field = field
        for child in field:
            if child.is_field_set:
                childnode = self.AppendItem(node, child.name)
                data.child_map[child.name] = childnode
                self.setup_new_node(childnode, child)
        data.enumerated = True

    def find_node(self, field):
        path = field.path
        curfield = field['/']
        curnode = self.root
        for seg in path.split('/'):
            if seg:
                curfield = curfield[seg]
                curnode = self.GetItemData(curnode).child_map[seg]
            data = self.GetItemData(curnode)
            if data.enumerated:
                continue
            self.enumerate_node(curnode, curfield)
        return curnode

    def update_root_name(self):
        if self.root is not None:
            self.SetItemText(self.root, self.filename)

    def OnExpand(self, event):
        data = self.GetItemData(event.Item)
        if not data.enumerated:
            self.enumerate_node(event.Item, data.field)

    def OnActivate(self, event):
        data = self.GetItemData(event.Item)
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
        node = self.find_node(field)
        self.Expand(node)
        self.SelectItem(node)
        self.ScrollTo(node)
