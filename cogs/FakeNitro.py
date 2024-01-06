# # base stuff
# import requests
#
# # discord libraries
# import discord
# from discord import Guild
# from collections import deque
#
# from discord.ext import commands
#
# from discord_slash import SlashCommand, SlashContext
# from discord_slash import cog_ext
# from discord_slash.cog_ext import cog_component
# from discord_slash.utils.manage_commands import create_option, create_choice

from interactions import Client, Extension, slash_command, SlashCommandOption, OptionType, SlashContext

import time
from re import search
from random import randint
import json

# blacklisted servers where emotes aren't read (e.g. my dev servers)
# bl_servers = ["ohhh"]
bl_servers = []

# Mong ID 395243617956003842
scopes = [395243617956003842]

def ret_e_name(e):
    return str(e.name)

# invoked msgs dict,
# key = invoked user id
# value = the command message (from the bot) from that user (id only?)
invo_msgs = {}

class FakeNitro(Extension):
    def __init__(self, client):
        self.client: Client = client

    @slash_command(name="concat",
                 description="Concatenate a message with fake nitro emotes.",
                 scopes=scopes,
                 options=[
                    SlashCommandOption(
                        name="names",
                        description="Usage: Type in emote names separated by comma. ~ for new line. e.g. eblangled,blank,~,eblangledL.",
                        type=OptionType.STRING,
                        required=True
                    )

                ])
    async def concat(self, ctx: SlashContext, names:str):
        # buy time
        await ctx.defer()

        names_spl = names.split(",")
        send = ""
        not_found = False

        emotes_json = json.load(open('emojis.json'))
        emojis = emotes_json["emojis"]
        shortnames = [i["shortname"] for i in emojis]
        # print(shortnames)
        for name in names_spl:
            if name == "~":
                send = send + "\n"
            else:
                matched = False
                if ":" + name + ":" in shortnames:
                    send = send + ":"+name+":"
                    continue
                for g in self.client.guilds:
                    g_emo = await g.fetch_all_custom_emojis()
                    for e in g_emo:
                        if e.name.lower() == name.strip().lower():
                            send = send + str(e)
                            matched = True

                if not matched:
                    send = send + "`"+name+"` "
                    not_found = True
        # at the end, Send
        if not_found:
            await ctx.send("One or more of your inputs were not found. Please check the spelling, this command searches exact and complete names, not partial (e.g. for `eblangled`, 'eblan' will not match). The emotes not found are shown below in text. You can use /fnlist to see a list of all emotes. \n"+send,ephemeral=True)
        else:
            m = await ctx.send(send)
            invo_msgs[str(ctx.author.id)] = m

    @slash_command(name="fn",
                 description="Fake Nitro tool",
                 scopes=scopes,
                 options=[
                    SlashCommandOption(
                        name="name",
                        description="Emote name to search for",
                        type=OptionType.STRING,
                        required=True
                    ),
                    SlashCommandOption(
                        name="large",
                        description="Larger version of the emote?",
                        type=OptionType.STRING,
                        required=False
                    )
                ])
    async def fn(self, ctx: SlashContext, name:str, large:bool=False):
        if len(name) < 3:
            await ctx.send("Search term must be longer than 2 letters.", ephemeral=True)
        else:
            matched = []
            # print(type([0]))
            # self.client.http.get_self_guilds()
            for g in self.client.guilds:
                if g.name in bl_servers:
                    continue
                # print(g.emojis, g.name)
                g_emo = await g.fetch_all_custom_emojis()
                for e in g_emo:
                    # print(name.strip().lower() + " " + e.name.lower())
                    if search(name.strip().lower(), e.name.lower()):
                        # if the command is invoked from a server, AND the matched emote is from that server, AND it isn't animated
                        # meaning that you don't need nitro to use the emote anyway so skip it
                        if ctx.guild is not None and g.id == ctx.guild.id and not e.animated:
                            continue
                        # print("appended")
                        matched.append(e)
            # if matched at least one emote
            if len(matched) > 0:
                e = matched[randint(0,len(matched)-1)]
                if large:
                    ext = ".png"
                    if e.animated:
                        ext = ".gif"
                    m = await ctx.send("https://cdn.discordapp.com/emojis/"+str(e.id)+ext)
                else:
                    m = await ctx.send(str(e))
                print(ctx.author.id)
                invo_msgs[str(ctx.author.id)] = m
            else:
                # msgs.append(await ctx.send("No similar matching emotes found, try harder or use /fnlist for a full list.", delete_after=3))
                await ctx.send("No similar matching emotes found, try harder or use /fnlist for a full list.", ephemeral=True)

    @slash_command(name="de", scopes=scopes, description="Deletes the previous emote you sent with the bot")
    async def de(self, ctx):
        if str(ctx.author.id) in invo_msgs:
            m = invo_msgs[str(ctx.author.id)]
            if m:
                invo_msgs[str(ctx.author.id)] = None
                await m.delete()
                await ctx.send("Deleted.",ephemeral=True)
            else:
                await ctx.send("Can only delete immediate previous emote.", ephemeral=True)
        else:
            await ctx.send("No previous /fn usage recorded from you.", ephemeral=True)


    @slash_command(name="fnlist", scopes=scopes, description="Sends you a list of available emotes")
    async def fnlist(self, ctx):
        await ctx.send("Sending...", ephemeral=True)
        e_send_count = 100
        char_count = 0

        for g in self.client.guilds:
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
            await ctx.send(embeds=interactions.Embed(title=g.name, color=interactions.Color.red()), ephemeral=True)
            for e in sorted(g.emojis, key=ret_e_name):
                e_string = e_string + str(e)
                emote_count+=1
                char_count += len(str(e))
                if emote_count >= e_send_count or char_count > 1900:
                    await ctx.send(e_string, ephemeral=True)
                    emote_count = 0
                    char_count = 0
                    e_string = ""

            if emote_count != 0:
                await ctx.send(e_string, ephemeral=True)

        await ctx.send("End of list", ephemeral=True)
