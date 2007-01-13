# -*- coding: utf-8 -*-

class dispatcher_t:
    def __init__(self):
        self.receivers = []

    def add(self, who):
        self.add_sender(who)
        self.add_receiver(who)

    def add_sender(self, sender):
        sender.dispatcher = self

    def add_receiver(self, receiver):
        self.receivers.append(receiver)

    def trigger(self, event_name, *args):
        handler_name = 'on_' + event_name
        unhandled_name = 'on_unhandled'

        for receiver in self.receivers:
            if hasattr(receiver, handler_name):
                getattr(receiver, handler_name)(self, *args)
            elif hasattr(receiver, unhandled_name):
                getattr(receiver, unhandled_name)(self, event_name, *args)
