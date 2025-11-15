# this cog checks if the user doesn't know and reacts with an emoji mocking them for their lack knowledge
# works only on a specific guild
# checks for sentences such as "idk", "I don't know", "I'm not of understandment"(inside joke), and many others

import interactions
import re
import random

def get_mocking_level():
    roll = random.random()
    if roll < 0.005:
        return "ultimate"
    elif roll < 0.005 + 0.05:
        return "message"
    elif roll < 0.005 + 0.05 + 0.2:
        return "reaction"
    else:
        return "hidden"

class Idk(interactions.Extension):
    @interactions.listen()
    async def on_message_create(self, event: interactions.Message):
        
        if event.message.author.bot:
            return

        mock_emote="<:lookatthisdude:1437147304044789963>"
        regex_pattern = r"\b(idk|dunno|beats\sme|no\sclue|no\sidea)\b|i(?:\s*(?:'m|am))?\s*(?:(?:do\s?n[o']t|not|am\snot)\s+(?:(?:really|even|quite)\s+)?(?:know|get|understand|see)|(?:have(?:\s+got)?|got)\s+no\s+(?:idea|clue|inkling))|i(?:\s*(?:'m|am))?\s*(?:not|un)(?:sure|certain|clear)|i\s+lack\s+(?:(?:critical|important)|(?:the\s+)?(?:necessary\s+)?)information|i(?:\s*(?:'m|am))\s+not\s+of\s+understandment"
        if event.message.guild.id == 395243617956003842 and re.search(regex_pattern, event.message.content.lower()):
            mocking_level = get_mocking_level()
            if mocking_level == "hidden":
                #do nothing
                #print("hidden mocking triggered")
                return
            elif mocking_level == "ultimate":
                #send spam of messages and gifs
                #might be super cringe, should improve this later
                await event.message.reply("https://tenor.com/view/announcer-announcer-meme-awful-opinion-awful-take-bad-opinion-gif-925753956088699311")
                await event.message.channel.send("Guys, look at this dude! " + event.message.author.mention + " doesn't know!")
                await event.message.channel.send("https://tenor.com/view/laugh-at-this-user-ryan-gosling-ryan-gosling-cereal-embed-fail-meme-gif-22090542")
                await event.message.channel.send(mock_emote)
                await event.message.channel.send("https://tenor.com/view/pepe-laugh-he-doesnt-know-pepe-gif-14019260")
                await event.message.channel.send("https://tenor.com/view/sopranos-sopranos-paulie-laughing-the-sopranos-tony-soprano-gif-11977582283759302788")
                #print("ultimate mocking triggered")
            elif mocking_level == "message":
                #send message
                await event.message.reply("He doesn't know! " + mock_emote)
                #print("message mocking triggered")
            elif mocking_level == "reaction":
                #send reaction
                await event.message.add_reaction(mock_emote)
                #print("reaction mocking triggered")



def setup(bot):
    Idk(bot)
    