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
    cal = None
    offline_message = None

    # --- Calendar Fetching Logic ---
    url = "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
    local_ics_filename = url.split('/')[-1]
    local_ics_file_path = f"/home/timlau_cy/{local_ics_filename}" 
    cal_content = None

    # Try to fetch the live calendar up to 10 times
    for attempt in range(10):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            cal_content = response.text
            break # Success on fetch
        except requests.exceptions.RequestException:
            time.sleep(0.1) # Short delay before retrying
    
    if cal_content:
        # We successfully fetched the content from the web
        print(f"Successfully fetched live calendar in {attempt + 1} attempt(s).")
        cal = Calendar(cal_content)
        try:
            with open(local_ics_file_path, 'w', encoding='utf-8') as f:
                f.write(cal_content)
        except IOError as e:
            print(f"Warning: Could not write to local ICS cache '{local_ics_file_path}': {e}")
    else:
        # All attempts to fetch from web failed, so fall back to local copy
        print(f"Failed to fetch live calendar from '{url}' after 10 attempts. Attempting to use local cache.")
        try:
            last_updated_timestamp = int(os.path.getmtime(local_ics_file_path))
            with open(local_ics_file_path, 'r', encoding='utf-8') as f:
                local_cal_content = f.read()
            cal = Calendar(local_cal_content)
            offline_message = f"⚠️ **Calendar Offline**: Using local backup, last updated <t:{last_updated_timestamp}:R>."
        except FileNotFoundError:
            print(f"Error: Local ICS cache not found at '{local_ics_file_path}'. Cannot display schedule.")
            error_msg = "The online calendar is currently down and a local backup could not be found."
            return None, error_msg
    
    if not cal:
        print("Error: Calendar object could not be created from either online or local source.")
        error_msg = "Could not parse calendar data from the online or local source."
        return None, error_msg

    # --- Embed Building Logic ---
    max_n = args[0] if args and 0 < args[0] <= 10 else 1

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
    embed = interactions.Embed(title=title, color=interactions.Color.random())

    events = list(cal.timeline.now()) + list(cal.timeline.start_after(now))

    # Filter events based on selected type
    if session_type != "all":
        filtered_events = []
        for ev in events:
            lines = ev.serialize().split("\n")
            summary = next((l for l in lines if l.startswith("SUMMARY:F1:")), "").split(":", 2)[2]
            lower_summary = summary.lower()
            
            should_add = False
            if session_type == "fp" and any(s in lower_summary for s in ["fp1", "fp2", "fp3"]):
                should_add = True
            elif session_type == "q" and "qualifying" in lower_summary:
                should_add = True
            elif session_type == "sp" and "sprint" in lower_summary:
                should_add = True
            elif session_type == "gp" and "grand prix" in lower_summary and not any(s in lower_summary for s in ["fp1", "fp2", "fp3", "qualifying", "sprint"]):
                should_add = True

            if should_add:
                filtered_events.append(ev)
        events = filtered_events

    for idx, ev in enumerate(events):
        if idx >= max_n:
            break
        lines = ev.serialize().split("\n")
        summary = next((l for l in lines if l.startswith("SUMMARY:F1:")), "").split(":",2)[2]
        start   = next((l for l in lines if l.startswith("DTSTART:")), "").split(":",1)[1]
        end     = next((l for l in lines if l.startswith("DTEND:")),   "").split(":",1)[1]

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
    
    return embed, offline_message


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
        three_days_from_now = now + timedelta(days=3)

        # --- MODIFICATION START: Cache ICS file locally with retries ---
        url = "https://files-f1.motorsportcalendars.com/f1-calendar_p1_p2_p3_qualifying_sprint_gp.ics"
        local_ics_filename = url.split('/')[-1]
        local_ics_file_path = f"/home/timlau_cy/{local_ics_filename}"
        cal = None
        cal_content = None

        # Try to fetch up to 10 times
        for attempt in range(10):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                cal_content = response.text
                break # Success on fetch
            except requests.exceptions.RequestException:
                await asyncio.sleep(0.1) # Small async delay before retrying
        
        if cal_content:
            # We successfully fetched the content from the web
            print(f"Reminder loop: Successfully fetched live calendar in {attempt + 1} attempt(s).")
            cal = Calendar(cal_content)
            try:
                with open(local_ics_file_path, 'w', encoding='utf-8') as f:
                    f.write(cal_content)
            except IOError as e:
                print(f"Warning: Could not write to local ICS cache for reminders '{local_ics_file_path}': {e}")
        else:
            # All attempts failed, so fall back to local copy
            print(f"Reminder loop: Failed to fetch live calendar after 10 attempts. Using local cache.")
            try:
                with open(local_ics_file_path, 'r', encoding='utf-8') as f:
                    local_cal_content = f.read()
                cal = Calendar(local_cal_content)
            except FileNotFoundError:
                print(f"Reminder loop error: Local ICS cache not found at '{local_ics_file_path}'. Skipping.")
                return
        # --- MODIFICATION END ---

        if not cal:
            print("Reminder loop error: Calendar object could not be created. Skipping.")
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
    async def f1_schedule(self, ctx: SlashContext, type: str = "all", max: int = 1):
        if max <= 0:
            max = 1
        
        embed, message = get_f1_schedule(type, max)

        # Handle hard failures where no embed can be generated
        if embed is None:
            if message:
                await ctx.send(message, ephemeral=True)
            else:
                await ctx.send("An unknown error occurred while fetching the F1 schedule.", ephemeral=True)
            return

        # In the normal case, send the schedule embed publicly
        await ctx.send(embeds=embed)
        
        # If there's an accompanying message (like the offline warning), send it as an ephemeral followup
        if message:
            await ctx.send(message, ephemeral=True, delete_after=5)

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

