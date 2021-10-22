import discord
from discord import Client, Channel, Embed

import os
import asyncio

TOKEN = os.getenv("BOT_TOKEN")

client = Client(TOKEN)
test_channel_id = 873181947583660054
channel = Channel(test_channel_id, client.get_token)

embed = Embed(title = "Hello!", description = "Hi!")
embed.create_field(name = "This is a field name", value = "This is a field value")

asyncio.run(channel.send(message = "Hi!", embed = embed))