# this cog checks if the user doesn't know and reacts with an emoji mocking them for their lack knowledge
# works only on a specific guild
# checks for sentences such as "idk", "I don't know", "I'm not of understandment"(inside joke), and many others

import interactions
import re

class Idk(interactions.Extension):
    @interactions.listen()
    async def on_message_create(self, event: interactions.Message):
        if event.message.author.bot:
            return

        regex_pattern = r"\b(idk|dunno|beats\sme|no\sclue|no\sidea)\b|i(?:\s*(?:'m|am))?\s*(?:(?:do\s?n[o']t|not|am\snot)\s+(?:(?:really|even|quite)\s+)?(?:know|get|understand|see)|(?:have|got)\s+no\s+(?:idea|clue|inkling))|i(?:\s*(?:'m|am))?\s*(?:not|un)(?:sure|certain|clear)|i\s+lack\s+(?:the\s+)?(?:necessary\s+)?information|i(?:\s*(?:'m|am))\s+not\s+of\s+understandment"
        if event.message.guild.id == 395243617956003842 and re.search(regex_pattern, event.message.content.lower()):
            try:
                await event.message.add_reaction("<:lookatthisdude:1323247099344715796>")
            except:
                pass


def setup(bot):
    Idk(bot)
    