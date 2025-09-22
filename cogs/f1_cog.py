import os
import json
import asyncio
import requests
import time

from datetime import datetime, timezone, timedelta
from ics import Calendar
import dateutil.parser

import interactions
from interactions import (
    Extension, 
    slash_command, SlashCommandOption, SlashCommandChoice, OptionType,
    SlashContext
)

# ---- CONFIG ----
SCOPES          = [395243617956003842]
F1_ROLE_MENTION = "<@&571262336497614868>"
CHANNEL_ID      = 396094614307864591
REMINDER_FILE   = "scheduled_reminders.json"


# ---- HELPER: Build the F1 schedule embed ----
def get_f1_schedule(session_type, *args):
    emoji_fp    = ":man_in_motorized_wheelchair:"
    emoji_quali = ":stopwatch:"
    emoji_gp    = ":race_car:"
    emoji_sp    = ":man_running_tone5:"
    now = datetime.now(timezone.utc)
    offline = False
    cal = None

    # choose calendar URL
    urls = {
        "fp":  "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3.ics",
        "q":   "https://files-f1.motorsportcalendars.com/f1-calendar_qualifying.ics",
        "gp":  "https://files-f1.motorsportcalendars.com/f1-calendar_gp.ics",
        "sp":  "https://files-f1.motorsportcalendars.com/f1-calendar_sprint.ics",
        "all": "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
    }
    url = urls.get(session_type, urls["all"])

    for _ in range(10):
        try:
            cal = Calendar(requests.get(url).text)
            break
        except Exception as e:
            print(_, e)
            time.sleep(0.05)

    if not cal:
        # if no work, assume calendar is down
        local_ics_file_path = "/home/timlau_cy/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
        # print(e)
        try:
            with open(local_ics_file_path, 'r', encoding='utf-8') as f:
                cal_content = f.read()
            cal = Calendar(cal_content)
            offline = True
        except FileNotFoundError:
            print(f"Local ICS file not found: {local_ics_file_path}. Everything is fucked, the end.")
            return

    # try:
    #     cal = Calendar(requests.get(url).text)
    # except Exception as e:
    #     # if no work, assume calendar is down
    #     local_ics_file_path = "/home/timlau_cy/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
    #     print(e)
    #     try:
    #         with open(local_ics_file_path, 'r', encoding='utf-8') as f:
    #             cal_content = f.read()
    #         cal = Calendar(cal_content)
    #         offline = True
    #     except FileNotFoundError:
    #         print(f"Local ICS file not found: {local_ics_file_path}. Everything is fucked, the end.")
    #         return

    # how many to show
    max_n = args[0] if args and 0 < args[0] <= 10 else 1

    # pretty name + emoji
    pretty_map = {
        "fp": ("Practice", emoji_fp),
        "q":  ("Qualifying", emoji_quali),
        "gp": ("GP", emoji_gp),
        "sp": ("Sprint", emoji_sp),
        "all": ("Session", ":checkered_flag:")
    }
    pretty, emoji = pretty_map.get(session_type, pretty_map["all"])

    if max_n > 1:
        title="Next "+ str(max_n) + " F1 " + pretty + "s " + emoji
    else:
        title="Next F1 " + pretty + " " + emoji
    # title = f"Next F1 {pretty}" + ("" if max_n == 1 else f"s ({max_n})") + f" {emoji}"
    embed = interactions.Embed(title=title, color=interactions.Color.random())

    events = list(cal.timeline.now()) + list(cal.timeline.start_after(now))
    for idx, ev in enumerate(events):
        if idx >= max_n:
            break
        lines = ev.serialize().split("\n")
        summary = next((l for l in lines if l.startswith("SUMMARY:F1:")), "").split(":",2)[2]
        start   = next((l for l in lines if l.startswith("DTSTART:")), "").split(":",1)[1]
        end     = next((l for l in lines if l.startswith("DTEND:")),   "").split(":",1)[1]

        # # if requested session type isn't such or ALL, but still in summary, skip
        # if session_type != "fp" or session_type != "all":
        #     if "FP1" in summary or "FP2" in summary or "FP3" in summary:
        #         continue
        # if session_type != "q" and session_type != "all":
        #     if "Qualify" in summary:
        #         continue
        # if session_type != "sp" and session_type != "all":
        #     if "Sprint" in summary:
        #         continue
        # if session_type != "gp" and session_type != "all":
        #     if "Grand Prix" in summary:
        #         continue

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

        dt_start = dateutil.parser.parse(start.rstrip("Z"))
        dt_end   = dateutil.parser.parse(end.rstrip("Z"))
        diff = dt_start - now

        if diff < timedelta(0):
            val = f"Live <t:{int(dt_start.timestamp())}:R>\nEnds <t:{int(dt_end.timestamp())}:R>"
        elif diff > timedelta(days=3):
            val = f"Starts <t:{int(dt_start.timestamp())}:F>"
        else:
            val = f"<t:{int(dt_start.timestamp())}:R> at <t:{int(dt_start.timestamp())}:t>"

        embed.add_field(name=summary, value=val, inline=False)
    
    if offline:
        embed.add_field(name="Calendar offline", value="-# Currently using local calendar last updated July 2025")

    return embed


# ---- THE COG ----
class FormulaOne(Extension):
    def __init__(self, client: interactions.Client):
        self.client = client
        # load persisted reminders
        self.scheduled_events = self._load_reminders()

    @interactions.listen()
    async def on_ready(self):
        print("[F1 Cog] Bot is ready. Starting reminder loop.")
        asyncio.create_task(self._reminder_loop())

    def _load_reminders(self) -> list[str]:
        if os.path.exists(REMINDER_FILE):
            try:
                return json.load(open(REMINDER_FILE))
            except json.JSONDecodeError:
                return []
        return []

    def _save_reminders(self):
        with open(REMINDER_FILE, "w") as f:
            json.dump(self.scheduled_events, f)

    async def _reminder_loop(self):
        await self.client.wait_until_ready()
        while True:
            try:
                await self._schedule_new_reminders()
                # print("setting new")
            except Exception as e:
                print("[F1 Reminder Loop Error]", e)
            await asyncio.sleep(1800)  # every 30 minutes

    async def _schedule_new_reminders(self):
        now = datetime.now(timezone.utc)
        # Define a timedelta for 3 days
        three_days_from_now = now + timedelta(days=3)


        # # --- MODIFICATION START ---
        # # Specify the path to your local ICS file for testing
        # local_ics_file_path = "H:/Downloads/test.ics" # <--- IMPORTANT: Change this to your actual file path

        # try:
        #     with open(local_ics_file_path, 'r', encoding='utf-8') as f:
        #         cal_content = f.read()
        #     cal = Calendar(cal_content)
        # except FileNotFoundError:
        #     print(f"[F1 Reminder] Local ICS file not found: {local_ics_file_path}. Falling back to online calendar.")
        #     url = "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
        #     cal = Calendar(requests.get(url).text)
        # except Exception as e:
        #     print(f"[F1 Reminder] Error loading local ICS file: {e}. Falling back to online calendar.")
        #     url = "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
        #     cal = Calendar(requests.get(url).text)
        # # --- MODIFICATION END ---

        url = "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
        try:
            cal = Calendar(requests.get(url).text)
        except:
            # if no work, assume calendar is down
            local_ics_file_path = "/home/timlau_cy/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"

            try:
                with open(local_ics_file_path, 'r', encoding='utf-8') as f:
                    cal_content = f.read()
                cal = Calendar(cal_content)
                offline = True
            except FileNotFoundError:
                print(f"Local ICS file not found: {local_ics_file_path}. Everything is fucked, the end.")
                return

        # Iterate through events starting after 'now'
        for ev in cal.timeline.start_after(now):
            # print(ev)
            lines = ev.serialize().split("\n")
            summary = next((l for l in lines if l.startswith("SUMMARY:F1:")), "").split(":",2)[2].strip()
            start   = next((l for l in lines if l.startswith("DTSTART:")), "").split(":",1)[1].rstrip("Z")
            
            # Use dateutil.parser.parse for more robust parsing
            dt_start = dateutil.parser.parse(start) 
            
            eid = f"{summary}|{dt_start.isoformat()}"

            # 1. Skip if already scheduled
            if eid in self.scheduled_events:
                continue
            
            # 2. New Logic: Schedule only events within the next 3 days
            if not (now < dt_start <= three_days_from_now):
                continue

            # 3. Enhanced Filter: Only schedule key sessions (Qualifying, Grand Prix, Sprint)
            #    and explicitly exclude Free Practice sessions.
            #    We make the comparison case-insensitive with .lower()
            lower_summary = summary.lower()
            if not any(k in lower_summary for k in ("qualifying", "grand prix", "sprint")):
                continue
            if any(k in lower_summary for k in ("fp1", "fp2", "fp3")):
                continue

            # Persist and schedule
            self.scheduled_events.append(eid)
            self._save_reminders()
            
            rem_time = dt_start - timedelta(minutes=5)
            if rem_time > now: # Ensure reminder time is in the future
                asyncio.create_task(self._send_reminder_at(rem_time, summary, eid))

    async def _send_reminder_at(self, when: datetime, summary: str, eid_to_remove: str):
        delay = (when - datetime.now(timezone.utc)).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            ch = await self.client.fetch_channel(CHANNEL_ID)
            await ch.send(f"{F1_ROLE_MENTION} :mega: **{summary.upper()}** STARTS IN 5 MINUTES :mega:")

            # Safely remove the event ID from the list
            if eid_to_remove in self.scheduled_events:
                self.scheduled_events.remove(eid_to_remove)
                self._save_reminders()
                print(f"[F1 Reminder] Removed scheduled reminder for: {summary}")

        except Exception as e:
            print("[F1 Reminder Send Error]", e)

    # — /f1 schedule —
    @slash_command(
        name="f1", description="Shows F1 information",
        scopes=SCOPES,
        sub_cmd_name="schedule", sub_cmd_description="Upcoming sessions",
        options=[
            SlashCommandOption(
                name="type", description="fp/q/sp/gp/all",
                type=OptionType.STRING, required=False,
                choices=[
                    SlashCommandChoice(name="Grand Prix",    value="gp"),
                    SlashCommandChoice(name="Qualifying",    value="q"),
                    SlashCommandChoice(name="Free Practice", value="fp"),
                    SlashCommandChoice(name="Sprint",        value="sp"),
                    SlashCommandChoice(name="All",           value="all"),
                ]
            ),
            SlashCommandOption(
                name="max", description="How many sessions (max 10)",
                type=OptionType.INTEGER, required=False
            )
        ]
    )
    async def f1_schedule(self, ctx: SlashContext, type: str = "", max: int = 0):
        if max <= 0: max = 1
        if not type:  type = "all"
        embed = get_f1_schedule(type, max)
        await ctx.send(embeds=embed)

    # — /f1 upcoming_reminders —
    @slash_command(
        name="f1", description="Shows F1 information",
        scopes=SCOPES,
        sub_cmd_name="upcoming_reminders",
        sub_cmd_description="List pending F1 reminders"
    )
    async def f1_upcoming(self, ctx: SlashContext):
        if not self.scheduled_events:
            return await ctx.send("No reminders scheduled.")
        emb = interactions.Embed(
            title="📅 Pending F1 Reminders",
            description="Sent 5 minutes before each session.",
            color=interactions.Color.random()
        )
        for eid in self.scheduled_events:
            summary, ts = eid.split("|", 1)
            dt = dateutil.parser.parse(ts)
            unix = int(dt.timestamp())
            emb.add_field(
                name=summary,
                value=f"<t:{unix}:F> (<t:{unix}:R>)",
                inline=False
            )
        await ctx.send(embeds=emb)

    # — /f1 clear_reminders —
    @slash_command(
        name="f1", description="Shows F1 information",
        scopes=SCOPES,
        sub_cmd_name="clear_reminders",
        sub_cmd_description="Wipe all pending reminders"
    )
    async def f1_clear(self, ctx: SlashContext):
        self.scheduled_events.clear()
        self._save_reminders()
        await ctx.send("✅ All F1 reminders cleared.")
