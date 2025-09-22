"""
Discord Cog: Quotes Extension (Interactions.py v5+)
- Reads quotes from a CSV (Author,keyword,quote,date_added)
- Slash commands:
    /addquote keyword quote -> add a new quote (writes to CSV)
    /listkeywords       -> list available keywords
    /randomquote        -> get a random quote from whole DB
    /qid id            -> view metadata for a specific quote by its #ID
- Prefix command:
    ... <keyword>   -> send a quote matching the keyword

Usage:
    In your main bot file, load the extension:
    bot.load_extension("quotes_cog", csv_path="mongquotes.csv")

Notes:
- This version is built for the `interactions` library (interactions.py v5+).
- The CSV is appended to when adding quotes; the in-memory index is updated.
- The prefix listener requires the MESSAGE CONTENT intent to be enabled for your bot.
"""

import csv
import os
import random
import asyncio
from datetime import datetime
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
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    normalized = {
                        k.strip(): (v or "").strip() for k, v in row.items()
                    }
                    # CSV line number is the list index + 2 (1 for 0-indexing, 1 for header)
                    normalized["line_number"] = i + 2
                    self.quotes.append(normalized)
                    kw = normalized.get("keyword", "").lower()
                    if kw:
                        self.keyword_index.setdefault(kw, []).append(i)
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
                # Write to CSV file first
                with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=DEFAULT_HEADERS)
                    writer.writerow(row)
                # Then update in-memory cache
                index = len(self.quotes)
                # The new line number is the current number of quotes + 2
                row["line_number"] = index + 2
                self.quotes.append(row)
                kw = row["keyword"].lower()
                if kw:
                    self.keyword_index.setdefault(kw, []).append(index)
                return row
            except Exception as e:
                raise RuntimeError(f"Failed to append quote: {e}")

    # ---------- Helpers ----------
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
        for quote in self.quotes:
            if quote.get("line_number") == quote_id:
                return quote
        return None

    def _format_quote(self, row: Dict[str, str]) -> str:
        quote_text = row.get("quote", "")
        line_num = row.get("line_number", "?")
        return f"`#{line_num}` {quote_text}"

    # ---------- Commands ----------
    @slash_command(name="randomquote", description="Get a random quote from the database")
    async def randomquote(self, ctx: SlashContext):
        picked = self._find_random_any()
        if not picked:
            await ctx.send("No quotes available yet.")
            return
        await ctx.send(self._format_quote(picked))

    @slash_command(name="qid", description="View metadata for a specific quote by its ID")
    @slash_option(
        name="id",
        description="The #ID of the quote you want to view",
        opt_type=OptionType.INTEGER,
        required=True,
    )
    async def qid(self, ctx: SlashContext, id: int):
        picked = self._find_by_id(id)
        if not picked:
            await ctx.send(f"No quote found with ID `#{id}`.", ephemeral=True)
            return

        author = picked.get("Author", "Unknown")
        keyword = picked.get("keyword", "N/A")
        date_str = picked.get("date_added")

        if date_str:
            try:
                dt_obj = datetime.fromisoformat(date_str)
                timestamp = int(dt_obj.timestamp())
                time_str = f"<t:{timestamp}:F>"
            except (ValueError, TypeError):
                time_str = date_str  # Fallback to plain string if parsing fails
        else:
            time_str = "Not available"

        response = (
            f"**Quote `#{id}` Info:**\n"
            f"> **Author:** {author}\n"
            f"> **Keyword:** `{keyword}`\n"
            f"> **Added:** {time_str}"
        )
        await ctx.send(response, ephemeral=True)

    @slash_command(name="addquote", description="Add a new quote to the CSV store")
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
    async def addquote(self, ctx: SlashContext, keyword: str, quote: str):
        if len(quote) > 2000:
            await ctx.send(
                "Quote is too long (Discord limit ~2000 characters).", ephemeral=True
            )
            return

        author_name = ctx.author.username

        try:
            new_quote = await self.append_quote(
                author=author_name, keyword=keyword, quote_text=quote
            )
            line_num = new_quote.get("line_number", "?")
            await ctx.send(
                f"`#{line_num}` added by **{author_name}** :anger_right: `{keyword}`:\n{quote}"
            )
        except Exception as e:
            await ctx.send(f"Failed to save quote: {e}", ephemeral=True)

    @slash_command(
        name="listkeywords",
        description="List all available keywords in a paginated view",
    )
    async def listkeywords(self, ctx: SlashContext):
        kws = sorted(self.keyword_index.keys())
        if not kws:
            await ctx.send("No keywords available yet.", ephemeral=True)
            return

        pages = []
        keywords_per_page = 50
        chunks = [
            kws[i : i + keywords_per_page] for i in range(0, len(kws), keywords_per_page)
        ]

        if len(chunks) == 1:
            description = ", ".join(f"`{kw}`" for kw in chunks[0])
            await ctx.send(f"**Available Keywords:**\n{description}", ephemeral=True)
            return

        for i, chunk in enumerate(chunks):
            description = ", ".join(f"`{kw}`" for kw in chunk)
            embed = Embed(
                title="Available Keywords",
                description=description,
                color=0x5865F2,  # Discord Blurple
                footer=f"Page {i + 1} of {len(chunks)}",
            )
            pages.append(embed)

        paginator = Paginator(client=self.bot, pages=pages)
        await paginator.send(ctx, ephemeral=True)

    # ---------- Message listener for prefix command ----------
    @listen()
    async def on_prefix_quote(self, event: interactions.events.MessageCreate):
        message = event.message
        prefix = "... "

        # Ignore messages from bots, in DMs, or that don't start with the prefix.
        if not isinstance(message.author, interactions.Member) or message.author.bot:
            return
        if not message.content or not message.content.startswith(prefix):
            return

        # Extract keyword from message
        parts = message.content[len(prefix) :].split()
        if not parts:
            return  # User only sent the prefix

        keyword = parts[0]

        # Find and send the quote
        picked = self._find_random_by_keyword(keyword)
        if picked:
            try:
                await message.channel.send(self._format_quote(picked))
            except Exception as e:
                print(
                    f"[QuotesCog] Failed to send prefix quote in channel {message.channel.id}: {e}"
                )


# This setup function is how the extension is loaded
def setup(bot: interactions.Client, **kwargs):
    QuotesCog(bot, **kwargs)

