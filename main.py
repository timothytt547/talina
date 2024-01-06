import interactions
from interactions import Client, Intents, listen, SlashContext
from interactions.api.events import MessageCreate

# base libraries
import os
import requests
import json
from datetime import datetime, timezone, timedelta
import dateutil.parser

# load token
from dotenv import load_dotenv
load_dotenv()

# init bot stuff
bot = Client(intents=Intents.DEFAULT)

@listen()
async def on_ready():
    print("Ready!")

@listen()
async def on_slash_command(ctx):
    print(ctx.author.name + ": " + ctx.name)

@listen()
async def on_message_create(event: MessageCreate):
    # Teisoku ID 888627926755577907
    if event.message.guild.id == 888627926755577907:
        # Test channel ID 890583644782071818
        # Teisoku #general ID 888627927388942400
        msg = await bot.http.get_channel_messages(888627927388942400, limit=4)

        # print(msg[0]["author"]["id"])
        # print(msg[1]["author"]["id"])
        # print(msg[2]["author"]["id"])
        # print(msg[3]["author"]["id"])
        msg_time = dateutil.parser.isoparse(msg[1]["timestamp"])
        difference = datetime.now(timezone.utc) - msg_time

        # if the most recently sent of the 4 messages (3 previous messages) are all by the same author
        # meaning author tried to send a 4th message in a row in short succession
        # also check if second most recent message was over a day ago
        # if not over a day ago, delete most recent message
        recent_author = msg[0]["author"]["id"]

        if all(recent_author == m["author"]["id"] for m in msg):
            print("YES")
            if difference < timedelta(days = 1):
                # print("delete")
                chn = await bot.fetch_channel(888627927388942400)
                del_msg = await chn.fetch_message(event.message.id)
                await del_msg.delete()

# sorry cow
for cog in os.listdir("./cogs"):
    if cog.endswith(".py") and not cog.startswith("_"):
        try:
            cog = f"cogs.{cog.replace('.py', '')}"
            bot.load_extension(cog)
            print(f"{cog[5:]} loaded successfully!")
        except Exception as e:
            print(f"{cog} cannot be loaded:")
            raise e

bot.start(token=os.environ['TOKEN'])
