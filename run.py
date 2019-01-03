from configparser import ConfigParser
from time import gmtime, strftime
from telethon import TelegramClient, events
from telethon.tl.functions import channels
import logging
import os
import re
import sys
import requests

logging.basicConfig(format="%(message)s", level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_file = "config.ini"

config = ConfigParser()
config.read(config_file)

api_id = config.getint("telethon", "api_id")
api_hash = config.get("telethon", "api_hash")

session_name = config.get("telethon", "session_name", fallback="default")

client = TelegramClient(session_name, api_id, api_hash)
prems_channels = [int(n) for n in config.get("prems", "channels").split(',')]
news_channels = [int(n) for n in config.get("news", "channels").split(',')]

@client.on(events.NewMessage)
async def forwarder(event):
    try:
        if event.message.to_id.channel_id in prems_channels:
            logger.debug([strftime("%Y-%m-%d %H:%M:%S", gmtime()), "forwardPremium", event.message.to_id.channel_id, event.message.message])
            await client.forward_messages(config.get("prems", "relay_channel"), event.message)
        
        if event.message.to_id.channel_id in news_channels:
            logger.debug([strftime("%Y-%m-%d %H:%M:%S", gmtime()), "forwardNews", event.message.to_id.channel_id, event.message.message])
            await client.forward_messages(config.get("news", "relay_channel"), event.message)
        
    except AttributeError:
        pass

client.start()

print('(Press Ctrl+C to stop this)')
client.run_until_disconnected()
