import interactions

# f1 cmd stuff
from datetime import datetime, timezone, timedelta
from ics import Calendar
import dateutil.parser


def quote(session_type, *args):
    return embed

class UseQuotes(interactions.Extension):
    def __init__(self, bot):
        self.bot = bot
    
    # should be able to get quote based on ID, and also keyword
    # /quote id:[] and /quote get:[], /quote add:[] later
    # /getquote keyword:, /qid id:, /addquote later
    @interactions.extension_command(name="quote",
                 description="Interact with quotes",
                 options=[
                    interactions.Option(
                        name="get",
                        description="Get quote based on keyword",
                        type=interactions.OptionType.STRING,
                    ),
                    interactions.Option(
                        name="max",
                        description="Sessions shown, up to a maximum of 10",
                        type=interactions.OptionType.INTEGER,
                        required=False
                    )
                ]
            )
    async def f1(self, ctx, type:str="all", max:int=1):
        embed = get_f1(type, max)
        await ctx.send(embed=embed)

def setup(bot):
    FormulaOne(bot)
