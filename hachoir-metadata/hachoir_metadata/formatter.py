from hachoir_core.i18n import _

NB_CHANNEL_NAME = {1: _("mono"), 2: _("stereo")}

def humanAudioChannel(value):
    return NB_CHANNEL_NAME.get(value, unicode(value))

def humanFrameRate(value):
    if isinstance(value, (int, long, float)):
        return _("%.1f fps") % value
    else:
        return value

