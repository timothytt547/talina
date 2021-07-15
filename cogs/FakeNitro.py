# base stuff
import requests

# discord libraries
import discord
from discord import Guild
from collections import deque

from discord.ext import commands

from discord_slash import SlashCommand, SlashContext
from discord_slash import cog_ext
from discord_slash.cog_ext import cog_component
from discord_slash.utils.manage_commands import create_option, create_choice

import time
from re import search

# blacklisted servers where emotes aren't read (e.g. my dev servers)
# bl_servers = ["ohhh"]
bl_servers = []

def ret_e_name(e):
    return str(e.name)

# invoked msgs dict,
# key = invoked user id
# value = the command message (from the bot) from that user (id only?)
invo_msgs = {}

class FakeNitro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="fn",
                 description="Fake Nitro tool",
                 options=[
                    create_option(
                        name="name",
                        description="Emote name to search for",
                        option_type=3,
                        required=True
                    ),
                    create_option(
                        name="large",
                        description="Larger version of the emote?",
                        option_type=5,
                        required=False
                    )
                ])
    async def fn(self, ctx, name:str, large:bool=False):
        if len(name) < 3:
            await ctx.send("Search term must be longer than 2 letters.", delete_after=3)
        else:
            found = False
            async for guild in self.bot.fetch_guilds():
                g = await self.bot.fetch_guild(guild.id)
                if g.name in bl_servers:
                    continue
                # print(g.emojis, g.name)
                for e in g.emojis:
                    # print(args[0].lower() + " " + e.name.lower())
                    if search(name.strip().lower(), e.name.lower()):
                        found = True
                        if large:
                            ext = ".png"
                            if e.animated:
                                ext = ".gif"
                            m = await ctx.send("https://cdn.discordapp.com/emojis/"+str(e.id)+ext)
                        else:
                            m = await ctx.send(str(e))
                        invo_msgs[str(ctx.author.id)] = m
                        break
                if found:
                    break

            if not found:
                # msgs.append(await ctx.send("No similar matching emotes found, try harder or use /fnlist for a full list.", delete_after=3))
                await ctx.send("No similar matching emotes found, try harder or use /fnlist for a full list.", delete_after=3)


    @cog_ext.cog_slash(name="de", description="Deletes the previous emote you sent with the bot")
    async def de(self, ctx):
        if str(ctx.author.id) in invo_msgs:
            m = invo_msgs[str(ctx.author.id)]
            if m:
                invo_msgs[str(ctx.author.id)] = None
                await m.delete()
                await ctx.send("Deleted.",delete_after=.001)
            else:
                await ctx.send("Can only delete immediate previous emote.", delete_after=3)
        else:
            await ctx.send("No previous /fn usage recorded from you.", delete_after=3)


    @cog_ext.cog_slash(name="fnlist", description="DM's you a list of available emotes")
    async def fnlist(self, ctx):
        await ctx.send("Sending...", delete_after=.001)
        e_send_count = 100
        char_count = 0

        async for guild in self.bot.fetch_guilds():
            g = await self.bot.fetch_guild(guild.id)
            # print(g.name)
            if g.name in bl_servers or not g.emojis:
                # print("skipped "+g.name)
                continue

            page = 0
            emote_count = 0

            e_string = ""
            # send 16 emotes per field?
            # if over 16 emotes, next field
            # if over 2000 characters, send and start new embed
            await ctx.author.send(embed=discord.Embed(title=g.name, color=discord.Color.red()))
            for e in sorted(g.emojis, key=ret_e_name):
                e_string = e_string + str(e)
                emote_count+=1
                char_count += len(str(e))
                if emote_count >= e_send_count or char_count > 1900:
                    await ctx.author.send(e_string)
                    emote_count = 0
                    char_count = 0
                    e_string = ""

            if emote_count != 0:
                await ctx.author.send(e_string)

        await ctx.author.send("End of list")


def setup(bot):
    bot.add_cog(FakeNitro(bot))
