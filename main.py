import discord
from discord.ext.commands import Bot
from discord import Guild
import os
import requests
import json
from datetime import datetime, timezone
from ics import Calendar
import dateutil.parser

from difflib import SequenceMatcher
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

# load token
from dotenv import load_dotenv
load_dotenv()

bot = Bot("$")

# f1 cmd idea:
# $f1 - no arguments - shows information about upcoming race
# $f1 [type] (fp, quali, race)
def get_f1(args):
    emoji_fp = ":man_in_motorized_wheelchair:"
    emoji_quali = ":stopwatch:"
    emoji_gp = "<a:PepegaDriving:847480054379970601>"
    if len(args) != 0:
        session_type = args[0].lower()
    else:
        session_type = ""

    list_max = 1

    if len(args) > 1:
        try:
            int(args[1])
            list_max = int(args[1])
            if list_max > 10:
                list_max = 10
        except:
            list_max = 1

    type_pretty = "Session"
    emoji = ":checkered_flag:"

    if session_type == "fp" or session_type == "practice":
        type_pretty = "Practice"
        emoji = emoji_fp
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_p1_p2_p3.ics").text)
    elif session_type == "quali" or session_type == "q":
        type_pretty = "Quali"
        emoji = emoji_quali
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_q.ics").text)
    elif session_type == "race" or session_type == "gp":
        type_pretty = "GP"
        # emoji = "<:YEP:847466518483959857>"
        emoji = emoji_gp
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_gp.ics").text)
    elif session_type == "all":
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_p1_p2_p3_q_gp.ics").text)
    else:
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_p1_p2_p3_q_gp.ics").text)
        try:
            int(args[0])
            list_max = int(args[0])
            if list_max > 10:
                list_max = 10
        except:
            list_max = 1

    if list_max > 1:
        embed=discord.Embed(title="Next "+ str(list_max) + " F1 " + type_pretty + "s " + emoji, color=discord.Color.red())
    else:
        embed=discord.Embed(title="Next F1 " + type_pretty + " " + emoji, color=discord.Color.red())

    now = datetime.now(timezone.utc)
    events = list(c.timeline.start_after(now))
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
        out = str(diff).split(".")[0].split(":")

        embed.add_field(name=summary, value="In "+out[0]+" hours and "+out[1]+" minutes", inline=False)

        count+=1

    return embed

@bot.command()
async def f1(ctx, *args):
    """Shows upcoming F1 event dates

    Usage:
        !f1 - Shows immediate upcoming session
        !f1 [session type] - Shows relevant sessions only
            (types accepted: fp, practice, q, quali, gp, race, all)
        !f1 [session type] [number] - Shows requested amount of upcoming events (max 10)
        !f1 [number] - Shows the next immediate x number of sessions (max 10)
    """
    embed = get_f1(args)
    await ctx.send(embed=embed)

@bot.command()
async def fn(ctx, *args):
    """Mongcoust Nuked Emotes and Animated Emotes "tool"
    """
    # nme_guild_id = 847466330440859648
    # # could expand to use args to fetch any server (bot is in) in the future
    # nme = await bot.fetch_guild(nme_guild_id)
    wl_servers = ["Mongcoust", "mong nuked emotes"]
    if len(args) == 0:
        await ctx.send("Input an emote name to search for.")
    else:
        max_similar = 0
        max_e = ""
        async for guild in bot.fetch_guilds():
            g = await bot.fetch_guild(guild.id)
            if g.name not in wl_servers:
                continue
            # print(g.emojis, g.name)
            for e in g.emojis:
                s = similar(e.name.lower(), args[0].lower())
                if s > max_similar:
                    max_e = e
                    max_similar = s

        if max_similar == 0:
            await ctx.send("No emotes found with that name. Try another term.")
        elif max_similar < 1:
            await ctx.send(str(max_e))
            await ctx.send("||`:"+max_e.name+":`||")
        else:
            await ctx.send(str(max_e))

    # print(nme.emojis)
    # for b in bot.emojis:
    #     print(str(b))
    # await ctx.send()

@bot.command()
async def fnlist(ctx):
    wl_servers = ["Mongcoust", "mong nuked emotes"]
    count = 0
    page = 0

    embeds = []
    embeds.append(discord.Embed(title="Emotes List", color=discord.Color.red()))

    async for guild in bot.fetch_guilds():
        g = await bot.fetch_guild(guild.id)
        # print(g.name)
        if g.name not in wl_servers:
            # print("skipped "+g.name)
            continue
        for e in g.emojis:
            if count > 2000:
                count = 0
                page+=1
                embeds.append(discord.Embed(title="", color=discord.Color.red()))
            if g.name == "Mongcoust":
                if not e.animated:
                    continue
            count += len(str(e))+len(e.name)
            embeds[page].add_field(name=str(e), value=e.name + ", " + g.name, inline=False)

    # print(page, len(embeds))
    for e in embeds:
        await ctx.author.send(embed=e)

@bot.command()
async def ping(ctx):
    """Shows bot latency to the server"""
    pong = await ctx.send("Pong!")
    delay = (pong.created_at - ctx.message.created_at).total_seconds() * 1000
    await pong.edit(content = f"Pong! `{int(delay)}ms`")
    print(f"Ping: {int(delay)}ms \t {ctx.message.author} \t {ctx.message.guild}")

bot.run(os.environ['TOKEN'])
