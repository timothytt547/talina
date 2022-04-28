# discord libraries
import discord
from discord import Guild

from discord.ext import commands
from discord.ext.commands import Bot

from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission
from discord_slash.model import SlashCommandPermissionType

# base libraries
import os
import requests
import json
from datetime import datetime, timezone

# load token
from dotenv import load_dotenv
load_dotenv()

# init bot stuff
bot = Bot("$")
slash = SlashCommand(bot, sync_commands=True)

@bot.event
async def on_ready():
    print("Ready!")

@bot.event
async def on_slash_command(ctx):
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

# client.run(os.environ['TOKEN'])
bot.run(os.environ['TOKEN'])
