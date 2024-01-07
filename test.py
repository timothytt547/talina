# import discord
# import datetime
# import requests
# import ics
# from discord.ext import commands

# import pytz

# utc=pytz.UTC

# # Discord Bot Token
# DISCORD_TOKEN = "ODQ2Mzk1MzAxMjcwOTEzMDQ0.YKu5DQ.Kqf3XLtgaUyrv5X404nwmmNyPMI"

# # Formula One Calendar URL
# CALENDAR_URL = "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"

# intents = discord.Intents.default()

# # Initialize Discord bot
# bot = commands.Bot(intents=intents, command_prefix="!")


# @bot.event
# async def on_ready():
#     print("Bot is ready!")


# @bot.command()
# async def next_sessions(ctx):
#     response = requests.get(CALENDAR_URL)
#     calendar = ics.Calendar(response.text)

#     now = datetime.datetime.now()
#     session_times = []
#     for event in calendar.events:
#         if event.begin > utc.localize(now):
#             session_times.append((event.begin, event.name))
#         if len(session_times) >= 10:
#             break

#     session_times_formatted = [
#         (session_time.strftime("%A, %B %d, %Y - %I:%M %p"), session_type)
#         for session_time, session_type in session_times
#     ]

#     message = "Upcoming Formula One Sessions:\n"
#     for i, (session_time_formatted, session_type) in enumerate(session_times_formatted):
#         message += f"{i+1}. {session_time_formatted} - {session_type}\n"

#     await ctx.send(message)


# bot.run(DISCORD_TOKEN)
