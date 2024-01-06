# base stuff
import requests
import interactions
from interactions import Client, Extension, slash_command, SlashCommandOption, SlashCommandChoice, OptionType, SlashContext

# f1 cmd stuff
from datetime import datetime, timezone, timedelta
from ics import Calendar
import dateutil.parser
from table2ascii import table2ascii, PresetStyle
import json
from re import search

table_style = PresetStyle.thin_double_rounded
first_col_heading = True

# Mong ID 395243617956003842
scopes = [395243617956003842]


# helper function to add lines on top of table
def add_top(line, line_length):
    if len(line) < line_length:
        insert = ""
        for i in range(int((line_length-len(line)-1)/2)):
            insert = insert + " "
        insert = insert + line
        for i in range(int((line_length-len(line)-1)/2)):
            insert = insert + " "
        if len(insert) < line_length-1:
            insert = insert + " "
        insert = insert + "\n"

    return insert

def get_f1_schedule(session_type, *args):
    # set emojis for f1 embed display
    emoji_fp = ":man_in_motorized_wheelchair:"
    emoji_quali = ":stopwatch:"
    emoji_gp = ":race_car:"
    emoji_sp = ":man_running_tone5:"

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
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3.ics").text)
    elif session_type == "q":
        type_pretty = "Quali"
        emoji = emoji_quali
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_qualifying.ics").text)
    elif session_type == "gp":
        type_pretty = "GP"
        emoji = emoji_gp
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_gp.ics").text)
    elif session_type == "sp":
        type_pretty = "Sprint"
        emoji = emoji_sp
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_sprint.ics").text)
    elif session_type == "all":
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics").text)
    else:
        c = Calendar(requests.get("https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics").text)

    if list_max > 1:
        embed=interactions.Embed(title="Next "+ str(list_max) + " F1 " + type_pretty + "s " + emoji, color=interactions.Color.random())
    else:
        embed=interactions.Embed(title="Next F1 " + type_pretty + " " + emoji, color=interactions.Color.random())

    # make a list of events
    # if there is an event happening now, add it first
    # add all events after now
    now = datetime.now(timezone.utc)
    events = []
    if list(c.timeline.now()):
        events = events + list(c.timeline.now())
    events = events + list(c.timeline.start_after(now))

    count = 0

    # for each event, get the summary of the event and display the time
    for e in events:
        if count >= list_max:
            break

        # s = str(e).split("\n")
        s = e.serialize().split("\n")

        summary = s[9].split(":")[2]
        if "FP1" in summary or "FP2" in summary or "FP3" in summary:
            summary = emoji_fp + " " + summary
        elif "Qualify" in summary:
            summary = emoji_quali + " " + summary
        elif "Sprint" in summary:
            summary = emoji_sp + " " + summary
        elif "Grand Prix" in summary:
            summary = emoji_gp + " " + summary
        else:
            summary = ":question: " + summary

        start_time = s[7].split(":")[1]
        end_time = s[4].split(":")[1]

        # convert string time to datetime objects
        d = dateutil.parser.isoparse(start_time[:len(start_time)-1])
        e = dateutil.parser.isoparse(end_time[:len(end_time)-1])
        diff = d - now

        # if timedelta is negative, assume the event is happening now
        if diff < timedelta(0):
            embed.add_field(name=summary, value="Live, started <t:"+str(d.timestamp())[:-2]+":R>\nEnd: <t:"+str(e.timestamp())[:-2]+":R>", inline=False)
        # if more than 7 days, display date using instead of actual time
        elif diff > timedelta(days = 3):
            embed.add_field(name=summary, value="Starting <t:"+str(d.timestamp())[:-2]+":F>", inline=False)
        else:
            out = str(diff).split(".")[0].split(":")
            embed.add_field(name=summary, value="<t:"+str(d.timestamp())[:-2]+":R>, at <t:"+str(d.timestamp())[:-2]+":t>", inline=False)

        count+=1

    return embed

def get_f1_standings(type, *args):
        # if there is no additional arguments, display default
        if len(args) == 0:
            list_max = 5
        elif args[0] > 99:
            list_max = 99
        elif args[0] < 0:
            list_max = 5
        else:
            list_max = args[0]

        # "End of list" footer
        eol = True

        if type == "driver":
            response = requests.get("https://ergast.com/api/f1/current/driverStandings.json")
            r = response.json()
            standings_json = r["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]

            # build table
            count = 0
            header = ["Pos", "Driver", "Points"]
            body = []
            for s in standings_json:
                if count >= list_max:
                    eol = False
                    break

                body.append([s["position"], s["Driver"]["givenName"]+" "+s["Driver"]["familyName"],s["points"]])
                count+=1
        elif type == "constructor":
            response = requests.get("https://ergast.com/api/f1/current/constructorStandings.json")
            r = response.json()
            standings_json = r["MRData"]["StandingsTable"]["StandingsLists"][0]["ConstructorStandings"]

            # build table
            count = 0
            header = ["Pos", "Constructor", "Points"]
            body = []
            for s in standings_json:
                # if tripped count, do not show "End of list" footer
                if count >= list_max:
                    eol = False
                    break

                body.append([s["position"], s["Constructor"]["name"],s["points"]])
                count+=1

        if not eol:
            body.append(["...", "...", "..."])
            
        output = table2ascii(
            header=header,
            body=body,
            style=table_style,
            first_col_heading=first_col_heading
        )

        return output

async def get_f1_results(ctx, name, max, full):
    # if there is no additional arguments, display default
    if not max:
        list_max = 5
    # can't be more than 50 drivers in a race right
    elif max > 50:
        list_max = 50
    elif max < 0:
        list_max = 5
    else:
        list_max = max

    if not full:
        full == False

    circuit_id = "last"

    # "End of list" footer
    eol = True


    # extract total race numbers
    response = requests.get("http://ergast.com/api/f1/current.json")
    r = response.json()
    total_races = r["MRData"]["total"]
    if name:
        # get circuits name to search
        response = requests.get("https://ergast.com/api/f1/current/circuits.json")
        r = response.json()
        circuits_json = r["MRData"]["CircuitTable"]["Circuits"]
        # for every circuit (of this season), add name,id pair to list
        circuits = [[c["circuitName"],c["circuitId"]] for c in circuits_json]
        # print(circuits)
        # for c in circuits_json:
        #     circuits.append([c["circuitName"],c["circuitId"]])

        # expected behaviour:
        # circuit id defaults to "last" (api gets latest race)
        # if there is a name input, search
        # if more than one result found, return message to be more specific
        # if no results found, return message also (both ephemeral)
        # if only one result found, set circuit id to that one

        matched = []


        for c in circuits:
            if search(name.strip().lower(), c[0].lower()):
                # print("appended")
                matched.append(c)

        if len(matched) > 1:
            await ctx.send("Search term matched more than one track, be more precise.", ephemeral=True)
            return
        elif len(matched) == 0:
            await ctx.send("No results found, try again.", ephemeral=True)
            return
        elif len(matched) == 1:
            circuit_id = matched[0][1]

    print(circuit_id)
    if circuit_id != "last":
        response = requests.get("https://ergast.com/api/f1/current/circuits/"+circuit_id+"/results.json")
    else:
        response = requests.get("https://ergast.com/api/f1/current/last/results.json")
    rj = response.json()

    try:
        race_json = rj["MRData"]["RaceTable"]["Races"][0]
    except IndexError:
        await ctx.send("There are no results for this race (yet).", ephemeral=True)
        return
    # race_json is data of current race instance
    race_name = race_json["season"]+" "+race_json["raceName"]
    race_num = race_json["round"]

    if full:
        header = ["Pos", "Driver", "Team", "Status", "Points"]
    else:
        header = ["Pos", "Driver", "Team"]
    body = []

    count = 0
    for r in race_json["Results"]:
        if count >= list_max:
            eol = False
            break

        if full:
            body.append([r["position"], r["Driver"]["givenName"]+" "+r["Driver"]["familyName"], r["Constructor"]["name"], r["status"], r["points"]])
        else:
            body.append([r["position"], r["Driver"]["givenName"]+" "+r["Driver"]["familyName"], r["Constructor"]["name"]])

        count+=1

    if not eol:
        if full:
            body.append(["...","","...", "...", ""])
        else:
            body.append(["...","...", "..."])
        output = table2ascii(
            header=header,
            body=body,
            style=table_style,
            first_col_heading=first_col_heading
        )
    else:
        output = table2ascii(
            header=header,
            body=body,
            style=table_style,
            first_col_heading=first_col_heading
        )

    # add title to top using math magic
    line_length = output.find('\n')
    # print(line_length, len(race_name))
    round_num_insert = add_top("Round "+race_num+"/"+total_races, line_length)
    race_name_insert = add_top(race_name, line_length)
    output = race_name_insert + round_num_insert + output
    # print(repr(output))
    return output
    
async def get_f1_circuits():
    response = requests.get("https://ergast.com/api/f1/current/circuits.json")
    r = response.json()
    circuits_json = r["MRData"]["CircuitTable"]["Circuits"]
    
    body = ""
    for c in circuits_json:
        body = body + (c["circuitName"] + " (" + c["Location"]["locality"]+ ", " + c["Location"]["country"]+")\n")

    
    return body

class FormulaOne(Extension):
    def __init__(self, client):
        self.client: Client = client

    @slash_command(name="f1",
        description="Shows F1 information",
        scopes=scopes,
        sub_cmd_name="schedule",
        sub_cmd_description="Show the upcoming F1 races",
        options=[
            SlashCommandOption(
                name="type",
                description="Practice, Qualifying, Race/GP, Sprint",
                type=OptionType.STRING,
                required=False,
                choices=[
                    SlashCommandChoice(
                        name="Grand Prix",
                        value="gp"
                    ),
                    SlashCommandChoice(
                        name="Qualifying",
                        value="q"
                    ),
                    SlashCommandChoice(
                        name="Free Practice",
                        value="fp"
                    ),
                    SlashCommandChoice(
                        name="Sprint",
                        value="sp"
                    ),
                    SlashCommandChoice(
                        name="All",
                        value="all"
                    )
                ]
            ),
            SlashCommandOption(
                name="max",
                description="Sessions shown, up to a maximum of 10",
                type=OptionType.INTEGER,
                required=False
            )
        ]
    )
    async def f1_schedule(self, ctx: SlashContext, type:str="", max:int=0):
        # if input is either no input or invalid input, set default for subcommand
        if max == 0:
            max = 1
        if type == "":
            type = "all"
        embed = get_f1_schedule(type, max)
        await ctx.send(embeds=embed)


    @slash_command(name="f1",
        description="Shows F1 information",
        scopes=scopes,
        sub_cmd_name="standings",
        sub_cmd_description="Show the current season's standings",
        options=[
            SlashCommandOption(
                name="type",
                description="Driver/Constructor",
                type=OptionType.STRING,
                required=True,
                choices=[
                    SlashCommandChoice(
                        name="Driver",
                        value="driver"
                    ),
                    SlashCommandChoice(
                        name="Constructor",
                        value="constructor"
                    )
                ]
            ),
            SlashCommandOption(
                name="max",
                description="Rankings shown, defaults to 5",
                type=OptionType.INTEGER,
                required=False
            )
        ]
    )
    async def f1_standings(self, ctx: SlashContext,type:str="", max:int=0):
        # buy time
        await ctx.defer()

        # if input is either no input or invalid input, set default for subcommand
        if max == 0:
            max = 5

        output = get_f1_standings(type, max)

        await ctx.send("```\n"+output+"\n```")

    @slash_command(name="f1",
        description="Shows F1 information",
        scopes=scopes,
        sub_cmd_name="results",
        sub_cmd_description="Show this season's race results (use /f1 circuits for circuit names)",
        options=[
            SlashCommandOption(
                name="name",
                description="Track name to search for, leave as empty for latest race",
                type=OptionType.STRING,
                required=False
            ),
            SlashCommandOption(
                name="max",
                description="Places shown, defaults to 5",
                type=OptionType.INTEGER,
                required=False
            ),
            SlashCommandOption(
                name="full",
                description="Show additional info (points and status), will break table on mobile",
                type=OptionType.BOOLEAN,
                required=False
            )
        ]
    )
    async def f1_results(self, ctx: SlashContext, type:str="", name:str="", max:int=0, full:bool=False):
        # buy time
        await ctx.defer()

        # if input is either no input or invalid input, set default for subcommand
        if max == 0:
            max = 5

        output = await get_f1_results(ctx, name, max, full)
        print(len(output))
        if output:
            try:
                await ctx.send("```\n"+output+"\n```")
            except interactions.errors.LibraryException:
                await ctx.send("Table too long to send, please reduce the number of lines", ephemeral=True)

    @slash_command(name="f1",
        description="Shows F1 information",
        scopes=scopes,
        sub_cmd_name="circuits",
        sub_cmd_description="Show the current season's race circuits",
        options=[],
    )
    async def f1_circuits(self, ctx: SlashContext):
        output = await get_f1_circuits()
        # print(len(output))
        await ctx.send("```\n"+output+"\n```", ephemeral=True)