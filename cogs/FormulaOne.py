# base stuff
import requests

# discord stuff
import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.utils.manage_commands import create_option, create_choice

# f1 cmd stuff
from datetime import datetime, timezone, timedelta
from ics import Calendar
import dateutil.parser


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

class FormulaOne(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="f1",
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
    async def f1(self, ctx, type:str, max:int=1):
        embed = get_f1(type, max)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(FormulaOne(bot))
