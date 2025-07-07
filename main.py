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
bot = Client(intents=Intents.DEFAULT | Intents.MESSAGE_CONTENT)

@listen()
async def on_ready():
    print("Ready!")


@interactions.listen()
async def on_command(self, ctx: interactions.SlashContext):
    print(ctx.author.name + ": " + ctx.name)

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
