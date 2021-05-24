import discord
from discord.ext.commands import Bot
import os
import requests
import json
from datetime import datetime, timezone
from ics import Calendar
import dateutil.parser

# load token
from dotenv import load_dotenv
load_dotenv()

bot = Bot("!")

# f1 cmd idea:
# $f1 - no arguments - shows information about upcoming race
# $f1 [type] (fp, quali, race)
def get_f1(type):
    if type == "fp" or type == "practice":
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_p1_p2_p3.ics").text)
    elif type == "quali":
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_q.ics").text)
    elif type == "race" or type == "gp":
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_gp.ics").text)
    else:
        c = Calendar(requests.get("https://f1calendar.com/download/f1-calendar_q_gp.ics").text)

    now = datetime.now(timezone.utc)

    events = list(c.timeline.start_after(now))

    count = 0
    list_max = 3

    embed=discord.Embed(title="Next F1 Events", color=discord.Color.red())

    for e in events:
        if count >= list_max:
            break

        s = str(e).split("\n")
        # type = s[2].split(":")[1]

        summary = s[9].split(":")[1]
        start_time = s[7].split(":")[1]

        # print(start_time)

        d = dateutil.parser.isoparse(start_time[:len(start_time)-1])
        diff = d - now
        out = str(diff).split(".")[0].split(":")

        embed.add_field(name=summary, value="In "+out[0]+" hours, "+out[1]+" minutes", inline=False)

        count+=1

    return embed

    # response = requests.get('http://ergast.com/api/f1/'+str(now.year)+'.json')
    # json_data = json.loads(response.text)
    # races = json_data["MRData"]["RaceTable"]["Races"]
    # for r in races:
    #     race_name = r["raceName"]
    #     race_date = r["date"]
    #     race_time = r["time"][:len(r["time"])-1]
    #     d = datetime.strptime(race_date+" "+race_time, "%Y-%m-%d %H:%M:%S")
    #     if d > now:
    #         diff = d - now
    #         break
    # out = str(diff).split(".")[0].split(":")
    #
    # return "The next race is "+race_name+", starting in "+out[0]+" hours, "+out[1]+" minutes"

# @Bot.event
# async def on_ready():
#     print('We have logged in as {0.user}'.format(bot))

# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
#
#     if message.content.startswith('$hello'):
#         await message.channel.send('Hello!')
#
#     if message.content.startswith('$f1'):
#         msg = get_f1()
#         await message.channel.send(msg)

@bot.command()
async def f1(ctx, *args):
    if len(args) == 0:
        embed = get_f1("")
    else:
        embed = get_f1(args[0])
    await ctx.send(embed=embed)

bot.run(os.environ['TOKEN'])
