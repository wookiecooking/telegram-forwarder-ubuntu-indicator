#!/usr/bin/env python3
import os
import signal
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
gi.require_version('AppIndicator3', '0.1')

from threading import Thread
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GObject
from configparser import ConfigParser
from time import gmtime, strftime
from telethon import TelegramClient, events
from telethon.tl.functions import channels
import json
import logging
import re
import sys
import requests
import time

path = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(filename="telegram_forwarder.log", format="%(message)s", level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_file = "config.ini"

config = ConfigParser()
config.read(config_file)

api_id = config.getint("telethon", "api_id")
api_hash = config.get("telethon", "api_hash")

session_name = config.get("telethon", "session_name", fallback="default")
client = TelegramClient(session_name, api_id, api_hash)
prems_channels = [int(n) for n in config.get("premiums", "channels").split(',')]
news_channels = [int(n) for n in config.get("news", "channels").split(',')]



def daemon(func):
    def wrapper(*args, **kwargs):
        if os.fork(): return
        func(*args, **kwargs)
        os._exit(os.EX_OK)
    return wrapper

class Indicator():
    def __init__(self):
        self.app = 'telegram_forwarder'
        path = os.path.dirname(os.path.abspath(__file__))
        self.indicator = appindicator.Indicator.new(self.app, os.path.abspath(path+"/icon.svg"), appindicator.IndicatorCategory.OTHER)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)       
        self.indicator.set_menu(self.create_menu())
        self.notify = notify.init(self.app)
        self.update = Thread(target=self.start_forwarding)
        self.update.setDaemon(True)
        self.update.start()

    def start_forwarding(self):
        notify.Notification.new("<b>Telegram_Forwarder</b>", "Started", None).show()
        @client.on(events.NewMessage)
        async def forwarder(event):
            try:
                if event.message.to_id.channel_id in prems_channels:
                    x = await client.get_entity(event.message.to_id.channel_id)
                    notify.Notification.new("<b>Premium Channel: "+ x.title +" </b>", event.message.message, None).show()
                    logger.debug([strftime("%Y-%m-%d %H:%M:%S", gmtime()), "forwardPremium", event.message.to_id.channel_id, event.message.message])
                    await client.forward_messages(config.get("premiums", "relay_channel"), event.message)
                if event.message.to_id.channel_id in news_channels:
                    x = await client.get_entity(event.message.to_id.channel_id)
                    notify.Notification.new("<b>News Forward: "+ x.title +" </b>", event.message.message, None).show()
                    logger.debug([strftime("%Y-%m-%d %H:%M:%S", gmtime()), "forwardNews", event.message.to_id.channel_id, event.message.message])
                    await client.forward_messages(config.get("news", "relay_channel"), event.message)
            except AttributeError:
                pass
                
        client.start()
        client.run_until_disconnected()

    def create_menu(self):
        menu = gtk.Menu()
        item_quit = gtk.MenuItem('Quit')
        item_quit.connect('activate', self.stop)
        menu.append(item_quit)
        menu.show_all()
        return menu

    def stop(self, source):
        gtk.main_quit()

@daemon
def main():
    Indicator()
    GObject.threads_init()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    gtk.main()

main()

