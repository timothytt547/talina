# rimg_cog.py
"""
RImg Cog for interactions.py using Brave Search API

Install requirements:
    pip install interactions.py aiohttp

Usage:
 - Put your BRAVE_API_KEY in an environment variable.
 - Load this extension: bot.load_extension("rimg_cog")

This cog now listens for any message starting with ".rimg " and responds with an embed
containing the first Brave Image Search result and two buttons to page through results.
"""

import os
import asyncio
from uuid import uuid4
from typing import List

import aiohttp
from interactions import (
    Extension,
    listen, # MODIFIED: Imported 'listen' decorator
    events, # MODIFIED: Imported 'events' for type hinting
    ActionRow,
    Button,
    ButtonStyle,
    Embed,
)
# MODIFIED: Imported PrefixedContext to manually create a context object from a message
from interactions.ext.prefixed_commands import PrefixedContext


# Switched from Google to Brave Search API
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")
# How many images to request (Brave's default is 20, we can request less)
IMG_SEARCH_COUNT = 8
# how long in seconds to keep the pager alive waiting for button presses
PAGER_TIMEOUT = 60


class RImgExtension(Extension):
    def __init__(self, bot):
        super().__init__()
        # nothing persistent needed here; wait_for_component keeps per-command state
        # but we keep a tiny in-memory cache just to optionally track active searches (not required)
        self._active_sessions = {}

    async def search_images(self, query: str) -> List[str]:
        """Use Brave Search API to get image links.
           Returns a list of image URLs (may be empty).
        """
        if not BRAVE_API_KEY:
            raise RuntimeError(
                "BRAVE_API_KEY environment variable is required."
            )

        url = "https://api.search.brave.com/res/v1/images/search"
        params = {
            "q": query,
            "count": str(IMG_SEARCH_COUNT),
            "safesearch": "off",  # Can be "off" or "strict"
        }
        headers = {
            "X-Subscription-Token": BRAVE_API_KEY,
            "Accept": "application/json"
        }

        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, params=params, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    # try to capture error message if available
                    txt = await resp.text()
                    raise RuntimeError(f"Brave API error {resp.status}: {txt}")
                data = await resp.json()

        # Brave API response structure is different from Google's
        items = data.get("results", [])
        links = []
        for it in items:
            # The direct image URL is in the 'properties' dictionary
            link = it.get("properties", {}).get("url")
            if link:
                links.append(link)
        return links

    def _build_embed(self, query: str, url: str, index: int, total: int) -> Embed:
        emb = Embed(
            title=f"Image result for: {query}",
            description=f"Result {index+1} / {total}",
        )
        emb.set_image(url=url)
        emb.set_footer(text=f"Requested by search — use ◀ ▶ to browse. Session times out after {PAGER_TIMEOUT}s.")
        return emb

    def _build_actionrow(self, disabled: bool = False):
        prev_btn = Button(
            style=ButtonStyle.SECONDARY,
            label="◀",
            custom_id="rimg_prev",
            disabled=disabled,
        )
        next_btn = Button(
            style=ButtonStyle.SECONDARY,
            label="▶",
            custom_id="rimg_next",
            disabled=disabled,
        )
        return [ActionRow(prev_btn, next_btn)]

    # --- MODIFICATION START ---
    # The @prefixed_command has been replaced with an @listen() event listener.
    @listen("on_message_create")
    async def on_rimg_message(self, event: events.MessageCreate):
        """
        Listens to all messages and triggers on messages starting with '.rimg '.
        """
        message = event.message
        
        # Ignore bots and messages that don't start with the command
        if message.author.bot or not message.content.lower().startswith(".rimg "):
            return
            
        # Manually create a context object to use methods like ctx.send()
        ctx = PrefixedContext.from_message(self.bot, message)
        
        # Extract the query from the message content
        # .removeprefix() is used to get everything after ".rimg "
        query = message.content.removeprefix(".rimg ").strip()

        if not query:
            await ctx.send("Usage: `.rimg <search terms>`", ephemeral=True)
            return

        # await ctx.send(f"Searching images for: **{query}** ...", ephemeral=False)

        try:
            images = await self.search_images(query)
        except Exception as e:
            await ctx.send(f"Error while searching: {e}", ephemeral=True)
            return

        if not images:
            await ctx.send(f"No images found for **{query}**.", ephemeral=True)
            return

        index = 0
        total = len(images)
        embed = self._build_embed(query, images[index], index, total)
        components = self._build_actionrow(disabled=False)

        # The message object returned by ctx.send is what we need to monitor for components
        response_message = await ctx.send(embeds=embed, components=components)

        session_id = str(uuid4())
        self._active_sessions[session_id] = {"query": query, "images": images}

        while True:
            try:
                component_evt = await self.client.wait_for_component(
                    messages=response_message, components=components, timeout=PAGER_TIMEOUT
                )
            except asyncio.TimeoutError:
                disabled_components = self._build_actionrow(disabled=True)
                try:
                    await response_message.edit(embeds=self._build_embed(query, images[index], index, total), components=disabled_components)
                except Exception:
                    pass
                self._active_sessions.pop(session_id, None)
                break

            comp_ctx = component_evt.ctx

            # This logic remains the same to check if the interactor is the original author
            # MODIFICATION: The following block has been removed to allow anyone to page.
            # try:
            #     invoker_id = ctx.author.id
            # except Exception:
            #     invoker_id = getattr(ctx, "user", None) and ctx.user.id
            # 
            # clicker_id = None
            # if hasattr(comp_ctx, "author") and getattr(comp_ctx, "author", None):
            #     clicker_id = comp_ctx.author.id
            # elif hasattr(comp_ctx, "user") and getattr(comp_ctx, "user", None):
            #     clicker_id = comp_ctx.user.id
            # 
            # if invoker_id is not None and clicker_id != invoker_id:
            #     try:
            #         await comp_ctx.send("Only the user who ran the search can page through results.", ephemeral=True)
            #     except Exception:
            #         try:
            #             await comp_ctx.defer(ephemeral=True)
            #         except Exception:
            #             pass
            #     continue
                
            pressed = getattr(comp_ctx, "custom_id", None)
            if not pressed:
                pressed = getattr(component_evt, "custom_id", None) or (getattr(component_evt, "data", {}) or {}).get("custom_id")

            if pressed == "rimg_next":
                index = (index + 1) % total
            elif pressed == "rimg_prev":
                index = (index - 1) % total
            else:
                try:
                    await comp_ctx.send("Unknown button.", ephemeral=True)
                except Exception:
                    pass
                continue

            new_embed = self._build_embed(query, images[index], index, total)
            try:
                await comp_ctx.edit_origin(embeds=new_embed, components=components)
            except Exception:
                try:
                    await response_message.edit(embeds=new_embed, components=components)
                except Exception:
                    try:
                        await comp_ctx.send("Couldn't update message (edit failed).", ephemeral=True)
                    except Exception:
                        pass

        self._active_sessions.pop(session_id, None)
    # --- MODIFICATION END ---


def setup(bot):
    """This function is called when the extension is loaded by bot.load_extension("rimg_cog")"""
    RImgExtension(bot)


