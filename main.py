# discord libraries
import discord
from discord.ext.commands import Bot
from discord import Guild
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice

# base libraries
import os
import requests
import json

# functions libraries
from datetime import datetime, timezone, timedelta
from ics import Calendar
import dateutil.parser
import time
from re import search

# load token
from dotenv import load_dotenv
load_dotenv()

# init bot stuff
bot = Bot("$")
slash = SlashCommand(bot, sync_commands=True)

@bot.event
async def on_ready():
    print("Ready!")

# f1 cmd idea:
# $f1 - no arguments - shows information about upcoming race
# $f1 [type] (fp, quali, race)
def get_f1(session_type, *args):
    emoji_fp = ":man_in_motorized_wheelchair:"
    emoji_quali = ":stopwatch:"
    emoji_gp = "<a:PepegaDriving:847480054379970601>"

    if len(args) == 0:
        list_max = 1
    else:
        list_max = args[0]

    type_pretty = "Session"
    emoji = ":checkered_flag:"

    if session_type == "fp":
        type_pretty = "Practice"
        emoji = emoji_fp
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_p1_p2_p3.ics").text)
    elif session_type == "q":
        type_pretty = "Quali"
        emoji = emoji_quali
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_q.ics").text)
    elif session_type == "gp":
        type_pretty = "GP"
        # emoji = "<:YEP:847466518483959857>"
        emoji = emoji_gp
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_gp.ics").text)
    elif session_type == "all":
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_p1_p2_p3_q_gp.ics").text)
    else:
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_p1_p2_p3_q_gp.ics").text)

    if list_max > 1:
        embed=discord.Embed(title="Next "+ str(list_max) + " F1 " + type_pretty + "s " + emoji, color=discord.Color.red())
    else:
        embed=discord.Embed(title="Next F1 " + type_pretty + " " + emoji, color=discord.Color.red())

    now = datetime.now(timezone.utc)
    events = []
    if list(c.timeline.now()):
        # print("now")
        events = events + list(c.timeline.now())
    events = events + list(c.timeline.start_after(now))
    count = 0

    for e in events:
        if count >= list_max:
            break

        s = str(e).split("\n")
        # type = s[2].split(":")[1]

        summary = s[9].split(":")[1]
        if "Practice" in summary:
            summary = emoji_fp + " " + summary
        elif "Qualify" in summary:
            summary = emoji_quali + " " + summary
        elif "Grand Prix" in summary:
            summary = emoji_gp + " " + summary

        start_time = s[7].split(":")[1]

        # print(start_time)

        d = dateutil.parser.isoparse(start_time[:len(start_time)-1])
        diff = d - now

        # if timedelta is negative, assume the event is happening now
        if diff < timedelta(0):
            embed.add_field(name=summary, value="Happening now", inline=False)
        else:
            out = str(diff).split(".")[0].split(":")
            embed.add_field(name=summary, value="In "+out[0]+" hours and "+out[1]+" minutes", inline=False)

        count+=1

    return embed

@slash.slash(name="f1",
             description="Shows upcoming F1 event dates/times",
             options=[
                create_option(
                    name="type",
                    description="Practice, Qualifying, Race/GP",
                    option_type=3,
                    required=True,
                    choices=[
                    create_choice(
                        name="Free Practice",
                        value="fp"
                        ),
                    create_choice(
                        name="Qualifying",
                        value="q"
                        ),
                    create_choice(
                        name="Grand Prix",
                        value="gp"
                        ),
                    create_choice(
                        name="All",
                        value="all"
                        )
                    ]
                ),
                create_option(
                    name="max",
                    description="Sessions shown, up to a maximum of 10",
                    option_type=4,
                    required=False
                )
            ]
        )
async def f1(ctx, type:str, max:int=1):
    embed = get_f1(type, max)
    await ctx.send(embed=embed)

# whitelisted servers for emotes to be used on
# blacklisted servers where emotes aren't read (e.g. my dev servers)
bl_servers = ["ohhh"]

async def nuke_messages(msgs, *args):
    if len(args) > 0:
        time.sleep(int(args[0]))
    for m in msgs:
        await m.delete()

@slash.slash(name="fn",
             description="Fake Nitro tool",
             options=[
                create_option(
                    name="name",
                    description="Emote name to search for",
                    option_type=3,
                    required=True
                )
            ]
        )
# @bot.command()
async def fn(ctx, name:str):
    # """Fake Nitro tool
    # """

    msgs = []

    # if len(args) == 0:
    #     msgs.append(await ctx.send("Input an emote name to search for."))
    if len(name) < 3:
        msgs.append(await ctx.send("Search term must be longer than 2 letters."))
    else:
        atta = False
        max_similar = 0
        max_e = ""
        async for guild in bot.fetch_guilds():
            g = await bot.fetch_guild(guild.id)
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

def ret_e_name(e):
    return str(e.name)


@slash.slash(name="fnlist", description="DM's you a list of available emotes")
async def fnlist(ctx):
    # """DM's you a list of available emotes
    # By default sends the max amount of emotes per message, which condenses the amount of messages but loses large emote viewing. To preview with larger emotes, use "$fnlist large".
    # """
    e_send_count = 100
    char_count = 0

    async for guild in bot.fetch_guilds():
        g = await bot.fetch_guild(guild.id)
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

@slash.slash(name="bigsmoke",
            description="Sends the Big Smoke cutscene")
async def bigsmoke(ctx, small:bool=True):
    # """Sends the Big Smoke cutscene
    #     Use '$bigsmoke small' to send a smaller sized version.
    # """
    g = await bot.fetch_guild(511874763531223040)
    smoke = []
    e_string = ""
    emote_count = 0
    e_send_count = 24

    if small:
        e_send_count = 32

    for e in g.emojis:
        if "twonumber9s" in e.name:
            smoke.append(e)
    for e in sorted(smoke, key=ret_e_name):
        e_string = e_string + str(e)
        emote_count+=1
        if emote_count % 8 == 0:
            e_string += "\n"
        if emote_count >= e_send_count:
            await ctx.send(e_string)
            emote_count = 0
            e_string = ""

    if emote_count != 0:
        await ctx.send(e_string)

# @bot.command()
# async def ping(ctx):
#     """Shows bot latency to the server"""
#     pong = await ctx.send("Pong!")
#     delay = (pong.created_at - ctx.message.created_at).total_seconds() * 1000
#     await pong.edit(content = f"Pong! `{int(delay)}ms`")
#     print(f"Ping: {int(delay)}ms \t {ctx.message.author} \t {ctx.message.guild}")
#
@slash.slash(name="link",
            description="Shows the link to add the bot to your own server")
async def link(ctx):
    await ctx.send("`https://discord.com/api/oauth2/authorize?client_id=722507276572950671&permissions=0&scope=bot%20applications.commands`")

# client.run(os.environ['TOKEN'])
bot.run(os.environ['TOKEN'])
