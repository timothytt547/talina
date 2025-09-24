"""
Discord Cog: Quotes Extension (Interactions.py v5+)
- Reads quotes from a CSV (Author,keyword,quote,date_added)
- Slash commands:
    /quote add keyword quote -> add a new quote (writes to CSV)
    /quote list              -> list available keywords
    /quote random            -> get a random quote from whole DB
    /quote info id           -> view quote metadata (author, date added)
- Message trigger: if a message starts with '... <keyword>', the bot sends a matching quote.

Usage:
    In your main bot file, load the extension:
    bot.load_extension("quotes_cog", csv_path="mongquotes.csv")

Notes:
- This version is built for the `interactions` library (interactions.py v5+).
- The CSV is appended to when adding quotes; the in-memory index is updated.
"""

import csv
import os
import random
import asyncio
import re
from datetime import datetime, timezone
from typing import Dict, List

import interactions
from interactions import (
    Extension,
    listen,
    slash_command,
    SlashContext,
    slash_option,
    OptionType,
    Embed,
    Timestamp,
)
from interactions.ext.paginators import Paginator

DEFAULT_HEADERS = ["Author", "keyword", "quote", "date_added"]


class QuotesCog(Extension):
    def __init__(self, bot: interactions.Client, csv_path: str = "/home/timlau_cy/mongquotes.csv"):
        self.bot = bot
        self.csv_path = csv_path
        self.lock = asyncio.Lock()
        self.quotes: List[Dict[str, str]] = []
        self.keyword_index: Dict[str, List[int]] = {}
        self.load_csv()
        print(f"QuotesCog loaded with CSV: {self.csv_path}")

    # ---------- CSV handling ----------
    def _ensure_csv_exists(self):
        folder = os.path.dirname(self.csv_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=DEFAULT_HEADERS)
                writer.writeheader()

    def load_csv(self):
        self._ensure_csv_exists()
        self.quotes.clear()
        self.keyword_index.clear()
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                # The first line of data is on line 2, after the header
                reader = csv.DictReader(f)
                for i, row in enumerate(reader, start=2):
                    normalized = {k.strip(): (v or "").strip() for k, v in row.items()}
                    normalized["line_number"] = i
                    self.quotes.append(normalized)
                    kw = normalized.get("keyword", "").lower()
                    if kw:
                        self.keyword_index.setdefault(kw, []).append(i - 2)
        except Exception as e:
            print(f"[Quotes] Failed to load CSV '{self.csv_path}': {e}")

    async def append_quote(
        self, author: str, keyword: str, quote_text: str
    ) -> Dict[str, str]:
        async with self.lock:
            self._ensure_csv_exists()
            date_str = datetime.utcnow().isoformat()
            row = {
                "Author": author.strip(),
                "keyword": keyword.strip(),
                "quote": quote_text.strip(),
                "date_added": date_str,
            }
            try:
                with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=DEFAULT_HEADERS)
                    writer.writerow(row)

                # Update in-memory cache
                index = len(self.quotes)
                new_quote_data = row.copy()
                new_quote_data["line_number"] = index + 2
                self.quotes.append(new_quote_data)

                kw = row["keyword"].lower()
                if kw:
                    self.keyword_index.setdefault(kw, []).append(index)
                return new_quote_data
            except Exception as e:
                raise RuntimeError(f"Failed to append quote: {e}")

    # ---------- Helpers ----------
    async def _process_emojis(self, text: str, guild: interactions.Guild | None) -> str:
        """
        Finds emoji strings (e.g., <:name:id>) or names (e.g., :name:) in text,
        and replaces them with the current, valid emoji string from the server.
        """
        if not guild:
            return text

        try:
            # Fetch the server's current emoji list
            guild_emojis = await guild.fetch_all_custom_emojis()
            if not guild_emojis:
                # If no emojis, just strip the old emoji format to the name
                return re.sub(r"<a?:(\w+):\d+>", r":\1:", text)

            emoji_map = {emoji.name: emoji for emoji in guild_emojis}

            def replacer(match):
                # Check which group was captured to get the emoji name.
                # group(1) is from <:name:id>, group(2) is from :name:
                emoji_name = match.group(1) or match.group(2)
                if not emoji_name:
                    return match.group(0)  # Should not happen, but safe fallback

                # Look up the emoji in the current server's list
                emoji = emoji_map.get(emoji_name)
                if emoji:
                    # If found, return the new, correct emoji string
                    animated_prefix = "a" if emoji.animated else ""
                    return f"<{animated_prefix}:{emoji.name}:{emoji.id}>"
                else:
                    # If not found on the server, return the plain text name
                    return f":{emoji_name}:"

            # The regex finds either full emoji strings OR just emoji names
            processed_text = re.sub(r"<a?:(\w+):\d+>|:(\w+):", replacer, text)
            return processed_text

        except Exception as e:
            print(f"Could not process emojis for guild {guild.id}: {e}")
            # On error, fallback to just showing the name
            return re.sub(r"<a?:(\w+):\d+>", r":\1:", text)


    def _find_random_by_keyword(self, keyword: str):
        kw = (keyword or "").lower().strip()
        idxs = self.keyword_index.get(kw)
        if not idxs:
            return None
        return self.quotes[random.choice(idxs)]

    def _find_random_any(self):
        if not self.quotes:
            return None
        return random.choice(self.quotes)

    def _find_by_id(self, quote_id: int):
        # Adjust for 0-based index and header row
        target_index = quote_id - 2
        if 0 <= target_index < len(self.quotes):
            return self.quotes[target_index]
        return None

    async def _format_quote(self, row: Dict[str, str], guild: interactions.Guild | None) -> str:
        line_number = row.get("line_number", "?")
        quote_text = row.get("quote", "")
        processed_text = await self._process_emojis(quote_text, guild)
        return f"`#{line_number}` {processed_text}"

    # ---------- Commands ----------
    @slash_command(name="quote", description="Commands for managing and viewing quotes")
    async def quote(self, ctx: SlashContext):
        # This base command will never be called directly with subcommands.
        pass

    @quote.subcommand(sub_cmd_name="add", sub_cmd_description="Add a new quote to the CSV store")
    @slash_option(
        name="keyword",
        description="A single word to trigger the quote",
        opt_type=OptionType.STRING,
        required=True,
    )
    @slash_option(
        name="quote",
        description="The quote text itself",
        opt_type=OptionType.STRING,
        required=True,
    )
    async def add(self, ctx: SlashContext, keyword: str, quote: str):
        if len(quote) > 1900:  # Adjusted for formatting
            await ctx.send(
                "Quote is too long (Discord limit ~2000 characters).", ephemeral=True
            )
            return

        author_name = ctx.author.username
        try:
            added_quote = await self.append_quote(
                author=author_name, keyword=keyword, quote_text=quote
            )
            line_num = added_quote.get("line_number", "?")
            processed_quote_text = await self._process_emojis(quote, ctx.guild)
            
            output_string = f"`#{line_num}` added by {author_name} :anger_right: {keyword}:\n{processed_quote_text}"
            # print(f"DEBUG: Sending addquote confirmation: {output_string}")
            await ctx.send(output_string)

        except Exception as e:
            await ctx.send(f"Failed to save quote: {e}", ephemeral=True)

    @quote.subcommand(sub_cmd_name="list", sub_cmd_description="List all available keywords (paginated)")
    async def list(self, ctx: SlashContext):
        kws = sorted(self.keyword_index.keys())
        if not kws:
            await ctx.send("No keywords available yet.", ephemeral=True)
            return

        items_per_page = 20
        # Group keywords into pages
        paged_keywords = [
            kws[i : i + items_per_page] for i in range(0, len(kws), items_per_page)
        ]

        if len(paged_keywords) <= 1:
            await ctx.send(f"Keywords: {', '.join(kws)}", ephemeral=True)
            return

        pages = []
        for i, page_kws in enumerate(paged_keywords, 1):
            embed = Embed(
                title="Available Keywords",
                description="\n".join(page_kws),
                color=0x7289DA,
                footer=f"Page {i}/{len(paged_keywords)}",
            )
            pages.append(embed)

        paginator = Paginator(client=self.bot, pages=pages)
        await paginator.send(ctx, ephemeral=True)

    @quote.subcommand(sub_cmd_name="random", sub_cmd_description="Get a random quote from the database")
    async def random(self, ctx: SlashContext):
        picked = self._find_random_any()
        if not picked:
            await ctx.send("No quotes available yet.")
            return
        
        keyword = picked.get("keyword", "unknown")
        quote_part = await self._format_quote(picked, ctx.guild)
        
        output_string = f"... {keyword}\n{quote_part}"

        # print(f"DEBUG: Sending randomquote: {output_string}")
        await ctx.send(output_string)

    @quote.subcommand(sub_cmd_name="info", sub_cmd_description="View a quote's metadata by its ID")
    @slash_option(
        name="id",
        description="The line number of the quote to look up",
        opt_type=OptionType.INTEGER,
        required=True,
    )
    async def info(self, ctx: SlashContext, id: int):
        quote = self._find_by_id(id)
        if not quote:
            await ctx.send(f"Could not find a quote with ID #{id}.", ephemeral=True)
            return

        author = quote.get("Author", "Unknown")
        keyword = quote.get("keyword", "None")
        date_str = quote.get("date_added", "N/A")

        # Extract just the date part from the string by splitting on space or T
        display_date = date_str.split(" ")[0].split("T")[0]

        embed = Embed(
            title=f"Metadata for Quote #{id}",
            color=0x1ABC9C,
        )
        embed.add_field(name="Author", value=author, inline=True)
        embed.add_field(name="Keyword", value=keyword, inline=True)
        embed.add_field(name="Date Added", value=display_date, inline=False)

        await ctx.send(embed=embed, ephemeral=True)

    # ---------- Message listener ----------
    @listen()
    async def on_message_create(self, event: interactions.events.MessageCreate):
        message = event.message
        # Ignore bots and DMs
        if message.author.bot or not isinstance(
            message.author, interactions.Member
        ):
            return

        content = message.content or ""
        prefix = "... "
        if not content.lower().startswith(prefix):
            return

        parts = content[len(prefix) :].split()
        if not parts:
            return

        keyword = parts[0]
        picked = self._find_random_by_keyword(keyword)
        if not picked:
            return

        try:
            output_string = await self._format_quote(picked, message.guild)
            # print(f"DEBUG: Sending from listener: {output_string}")
            await message.channel.send(output_string)
        except Exception as e:
            print(
                f"Listener failed to send quote for keyword '{keyword}': {e}"
            )


def setup(bot: interactions.Client, **kwargs):
    QuotesCog(bot, **kwargs)

