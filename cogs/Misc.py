# discord libraries
import discord
from discord import Guild

from discord.ext import commands
from discord.ext.commands import Bot

from discord_slash import SlashCommand, SlashContext
from discord_slash import cog_ext

def ret_e_name(e):
    return str(e.name)

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="bigsmoke",
                description="Sends the Big Smoke cutscene")
    async def bigsmoke(self, ctx):
        g = await self.bot.fetch_guild(511874763531223040)
        smoke = []
        e_string = ""
        emote_count = 0
        e_send_count = 24

        for e in g.emojis:
            if "twonumber9s" in e.name:
                smoke.append(e)
        for e in sorted(smoke, key=ret_e_name):
            e_string = e_string + str(e)
            emote_count+=1
            if emote_count % 8 == 0:
                e_string += "\n"
            # if emote_count >= e_send_count:
            #     await ctx.send(e_string)
            #     emote_count = 0
            #     e_string = ""

        if emote_count != 0:
            await ctx.send(e_string)

def setup(bot):
    bot.add_cog(Misc(bot))
