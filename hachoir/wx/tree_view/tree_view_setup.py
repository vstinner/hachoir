from hachoir.wx.resource import get_child_control


def setup_tree_view(parent, dispatcher):
    print("[+] Setup tree view")
    tree_view = get_child_control(parent, "tree_view")
    dispatcher.add_sender(tree_view)
    dispatcher.add(tree_view)
    dispatcher.add_receiver(tree_view)

    return tree_view
