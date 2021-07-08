# base stuff
import requests

# discord libraries
import discord
from discord import Guild

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

async def nuke_messages(msgs, *args):
    if len(args) > 0:
        time.sleep(int(args[0]))
    for m in msgs:
        await m.delete()

def ret_e_name(e):
    return str(e.name)

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
                    )
                ])
    async def fn(self, ctx, name:str):
        msgs = []

        # if len(args) == 0:
        #     msgs.append(await ctx.send("Input an emote name to search for."))
        if len(name) < 3:
            msgs.append(await ctx.send("Search term must be longer than 2 letters."))
        else:
            atta = False
            max_similar = 0
            max_e = ""
            async for guild in self.bot.fetch_guilds():
                g = await self.bot.fetch_guild(guild.id)
                if g.name in bl_servers:
                    continue
                # print(g.emojis, g.name)
                for e in g.emojis:
                    # print(args[0].lower() + " " + e.name.lower())
                    if search(name.lower(), e.name.lower()):
                        atta = True
                        # await ctx.send((ctx.author.nick if ctx.author.nick else str(ctx.author)[:len(str(ctx.author))-5])+":")
                        await ctx.send(str(e))
                        break
                if atta:
                    break

            if not atta:
                msgs.append(await ctx.send("No similar matching emotes found, try harder or use /fnlist for a full list."))

        await nuke_messages(msgs, 3)

    @cog_ext.cog_slash(name="fnlist", description="DM's you a list of available emotes")
    async def fnlist(self, ctx):
        # """DM's you a list of available emotes
        # By default sends the max amount of emotes per message, which condenses the amount of messages but loses large emote viewing. To preview with larger emotes, use "$fnlist large".
        # """
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
