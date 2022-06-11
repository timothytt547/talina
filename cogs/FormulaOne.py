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
    # set emojis for f1 embed display
    emoji_fp = ":man_in_motorized_wheelchair:"
    emoji_quali = ":stopwatch:"
    emoji_gp = "<a:PepegaDriving:847480054379970601>"
    emoji_sp = ":man_running::skin-tone-5:"

    # if there is no additional arguments, only display the immediate next event
    # else use user input
    if len(args) == 0:
        list_max = 1
    elif args[0] > 10:
        list_max = 10
    elif args[0] < 0:
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
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_qualifying.ics").text)
    elif session_type == "gp":
        type_pretty = "GP"
        emoji = emoji_gp
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_gp.ics").text)
    elif session_type == "sp":
        type_pretty = "Sprint"
        emoji = emoji_sp
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_sprint.ics").text)
    elif session_type == "all":
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics").text)
    else:
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics").text)

    if list_max > 1:
        embed=discord.Embed(title="Next "+ str(list_max) + " F1 " + type_pretty + "s " + emoji, color=discord.Color.red())
    else:
        embed=discord.Embed(title="Next F1 " + type_pretty + " " + emoji, color=discord.Color.red())

    # make a list of events
    # if there is an event happening now, add it first
    # add all events after now
    now = datetime.now(timezone.utc)
    events = []
    if list(c.timeline.now()):
        events = events + list(c.timeline.now())
    events = events + list(c.timeline.start_after(now))

    count = 0

    for e in events:
        if count >= list_max:
            break

        # print(e)

        s = str(e).split("\n")
        # type = s[2].split(":")[1]

        summary = s[9].split(":")[1]
        if "Practice" in summary:
            summary = emoji_fp + " " + summary
        elif "Qualify" in summary:
            summary = emoji_quali + " " + summary
        elif "Sprint" in summary:
            summary = emoji_sp + " " + summary
        elif "Grand Prix" in summary:
            summary = emoji_gp + " " + summary

        start_time = s[7].split(":")[1]

        # print(start_time)

        d = dateutil.parser.isoparse(start_time[:len(start_time)-1])
        diff = d - now

        #print(d)

        # if timedelta is negative, assume the event is happening now
        if diff < timedelta(0):
            embed.add_field(name=summary, value="Live now, started <t:"+str(d.timestamp())[:-2]+":R>", inline=False)
        # if more than 7 days, display date using instead of actual time
        elif diff > timedelta(days = 3):
            embed.add_field(name=summary, value="Starting <t:"+str(d.timestamp())[:-2]+":F>", inline=False)
        else:
            out = str(diff).split(".")[0].split(":")
            # embed.add_field(name=summary, value="In "+out[0]+" hours and "+out[1]+" minutes, at <t:"+str(d.timestamp())[:-2]+":t>", inline=False)
            embed.add_field(name=summary, value="<t:"+str(d.timestamp())[:-2]+":R>, at <t:"+str(d.timestamp())[:-2]+":t>", inline=False)
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
                        description="Practice, Qualifying, Race/GP, Sprint",
                        option_type=3,
                        required=False,
                        choices=[
                            create_choice(
                                name="Grand Prix",
                                value="gp"
                            ),
                            create_choice(
                                name="Qualifying",
                                value="q"
                            ),
                            create_choice(
                                name="Free Practice",
                                value="fp"
                            ),
                            create_choice(
                                name="Sprint",
                                value="sp"
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
    async def f1(self, ctx, type:str="all", max:int=1):
        embed = get_f1(type, max)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(FormulaOne(bot))
