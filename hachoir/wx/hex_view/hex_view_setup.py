from hachoir.wx.resource import get_child_control


def setup_hex_view(parent, dispatcher):
    print("[+] Setup hex view")
    hex_view = get_child_control(parent, 'hex_view')
    dispatcher.add_sender(hex_view)
    dispatcher.add(hex_view)
    dispatcher.add_receiver(hex_view)

    return hex_view
