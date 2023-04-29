import interactions

def get_f1(session_type, *args):
    return embed

class FormulaOne(interactions.Extension):
    def __init__(self, bot):
        self.bot = bot

    @interactions.extension_command(name="f1",
                 description="Shows upcoming F1 event dates/times",
                 options=[
                    interactions.Option(
                        name="type",
                        description="Practice, Qualifying, Race/GP, Sprint",
                        type=interactions.OptionType.STRING,
                        required=False,
                        choices=[
                            interactions.Choice(
                                name="Grand Prix",
                                value="gp"
                            ),
                            interactions.Choice(
                                name="Qualifying",
                                value="q"
                            )
                        ]
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
