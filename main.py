import interactions

# base libraries
import os
import requests
import json
from datetime import datetime, timezone

# load token
from dotenv import load_dotenv
load_dotenv()

# init bot stuff
bot = interactions.Client(token=os.environ['TOKEN'])

@bot.event
async def on_ready():
    print("Ready!")

@bot.event
async def on_slash_command(ctx):
    print(ctx.author.name + ": " + ctx.name)

@bot.command(
    name="reload",
    description="Reload Cogs",
    scope=447789315926261760,
    options=[
       interactions.Option(
           name="name",
           description="Cog to reload",
           type=interactions.OptionType.STRING,
           required=True
       )
   ]
)
async def reload_cog(ctx: interactions.CommandContext, name:str):
    await bot.reload("./cogs/"+name, name)

# sorry cow
for cog in os.listdir("./cogs"):
    if cog.endswith(".py") and not cog.startswith("_"):
        try:
            cog = f"cogs.{cog.replace('.py', '')}"
            bot.load(cog)
            print(f"{cog[5:]} loaded successfully!")
        except Exception as e:
            print(f"{cog} cannot be loaded:")
            raise e

bot.start()
