"""
Inline Query Module for FallenRobot
Supports: translate, urban dict, google search, wallpapers,
          music (Saavn/Deezer), paste, torrent, wiki, alive, pokedex
"""
import json
import socket
import sys
import time
from random import randint
from uuid import uuid4

import aiohttp
import requests
from googletrans import Translator
from telegram import (
    Update,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ParseMode,
)
from telegram.ext import CallbackContext, InlineQueryHandler

from FallenRobot import dispatcher, OWNER_ID

# ── Utilities ──────────────────────────────────────────────────────────────────

BOT_USERNAME = None  # filled at runtime in alive_result()


def _get_bot_username(context) -> str:
    global BOT_USERNAME
    if not BOT_USERNAME:
        BOT_USERNAME = context.bot.username
    return BOT_USERNAME


def _paste(content: str) -> str:
    """Upload text to hastebin."""
    try:
        resp = requests.post(
            "https://hastebin.com/documents",
            data=content.encode("utf-8"),
            timeout=10,
        )
        key = resp.json()["key"]
        return f"https://hastebin.com/{key}"
    except Exception:
        return "Error: Could not paste content."


def _time_convert(seconds: int) -> str:
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}:{sec:02d}"


# ── Result builders ────────────────────────────────────────────────────────────

def alive_result(context) -> InlineQueryResultPhoto:
    username = _get_bot_username(context)
    msg = (
        f"**Bot:** @{username}\n"
        f"**Status:** `Alive ✅`\n"
        f"**Python:** `{sys.version.split()[0]}`\n"
        f"**Platform:** `{sys.platform}`\n"
    )
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Main Bot", url=f"https://t.me/{username}"),
            InlineKeyboardButton("Go Inline", switch_inline_query_current_chat=""),
        ]
    ])
    return InlineQueryResultPhoto(
        id=str(uuid4()),
        title="Bot Alive",
        description="Check Bot Status",
        photo_url="https://telegra.ph/file/0bf1b29555518a0d45948.jpg",
        thumb_url="https://telegra.ph/file/0bf1b29555518a0d45948.jpg",
        caption=msg,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=buttons,
    )


def translate_results(lang: str, text: str) -> list:
    try:
        i = Translator().translate(text, dest=lang)
        msg = (
            f"__**Translated from {i.src} to {lang}**__\n"
            f"**Input:**\n{text}\n"
            f"**Output:**\n{i.text}"
        )
        return [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Translated to {lang}",
                description=i.text,
                input_message_content=InputTextMessageContent(msg),
            )
        ]
    except Exception as e:
        return [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Error",
                description=str(e),
                input_message_content=InputTextMessageContent(f"Translation error: {e}"),
            )
        ]


def urban_results(text: str) -> list:
    try:
        resp = requests.get(
            f"https://api.urbandictionary.com/v0/define?term={text}", timeout=8
        ).json()
        results = []
        for item in resp.get("list", [])[:8]:
            definition = item["definition"].replace("[", "").replace("]", "")
            example = item["example"].replace("[", "").replace("]", "")
            msg = (
                f"**Query:** {text}\n"
                f"**Definition:** __{definition}__\n"
                f"**Example:** __{example}__"
            )
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=item["word"],
                    description=definition[:100],
                    input_message_content=InputTextMessageContent(msg),
                )
            )
        return results or [_error_article("No results found for: " + text)]
    except Exception as e:
        return [_error_article(str(e))]


def google_results(text: str) -> list:
    try:
        resp = requests.get(
            f"https://ddg-api.herokuapp.com/search?query={text}&limit=8",
            timeout=8,
        ).json()
        results = []
        for item in resp:
            title = item.get("title", "No Title")
            link = item.get("href", "#")
            snippet = item.get("body", "")
            msg = f"[{title}]({link})\n{snippet}"
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=title,
                    description=snippet[:100],
                    input_message_content=InputTextMessageContent(
                        msg, disable_web_page_preview=True
                    ),
                )
            )
        return results or [_error_article("No results found for: " + text)]
    except Exception as e:
        return [_error_article(str(e))]


def wall_results(text: str) -> list:
    try:
        resp = requests.get(
            f"https://wall.alphacoders.com/api2.0/get.php?auth=YOUR_KEY&method=search&term={text}",
            timeout=8,
        ).json()
        results = []
        if resp.get("success"):
            for w in resp.get("wallpapers", [])[:8]:
                results.append(
                    InlineQueryResultPhoto(
                        id=str(uuid4()),
                        photo_url=w.get("url_image", ""),
                        thumb_url=w.get("url_thumb", ""),
                    )
                )
        return results or [_error_article("No wallpapers found for: " + text)]
    except Exception as e:
        return [_error_article(str(e))]


def saavn_results(text: str) -> list:
    try:
        resp = requests.get(
            f"https://saavn.dev/api/search/songs?query={text}&page=1&limit=5",
            timeout=8,
        ).json()
        results = []
        for song in resp.get("data", {}).get("results", []):
            title = song.get("name", "Unknown")
            album = song.get("album", {}).get("name", "Unknown")
            duration = _time_convert(song.get("duration", 0))
            artists = ", ".join(a["name"] for a in song.get("artists", {}).get("primary", []))
            dl_url = song.get("downloadUrl", [{}])[-1].get("url", "")
            caption = (
                f"**Title:** {title}\n"
                f"**Album:** {album}\n"
                f"**Duration:** {duration}\n"
                f"**Artists:** {artists}"
            )
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("▶ Play / Download", url=dl_url)]
            ]) if dl_url else None
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=title,
                    description=f"{album} | {duration} | {artists}",
                    input_message_content=InputTextMessageContent(
                        caption, disable_web_page_preview=True
                    ),
                    thumb_url=song.get("image", [{}])[-1].get("url", ""),
                    reply_markup=buttons,
                )
            )
        return results or [_error_article("No songs found for: " + text)]
    except Exception as e:
        return [_error_article(str(e))]


def paste_results(text: str) -> list:
    url = _paste(text)
    return [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Pasted!",
            description=url,
            input_message_content=InputTextMessageContent(
                f"**Paste Link:** {url}", disable_web_page_preview=True
            ),
        )
    ]


def torrent_results(text: str) -> list:
    try:
        resp = requests.get(
            f"https://apibay.org/q.php?q={text}&cat=0",
            timeout=10,
        ).json()
        results = []
        for item in resp[:8]:
            name = item.get("name", "Unknown")
            size_bytes = int(item.get("size", 0))
            size = f"{size_bytes / (1024**3):.2f} GB" if size_bytes > 1024**3 else f"{size_bytes / (1024**2):.2f} MB"
            seeds = item.get("seeders", "?")
            info_hash = item.get("info_hash", "")
            magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={name}"
            caption = (
                f"**Title:** __{name}__\n"
                f"**Size:** __{size}__\n"
                f"**Seeds:** __{seeds}__\n"
                f"**Magnet:** `{magnet}`"
            )
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=name,
                    description=f"{size} | Seeds: {seeds}",
                    input_message_content=InputTextMessageContent(
                        caption, disable_web_page_preview=True
                    ),
                )
            )
        return results or [_error_article("No torrents found for: " + text)]
    except Exception as e:
        return [_error_article(str(e))]


def wiki_results(text: str) -> list:
    try:
        resp = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{text}",
            timeout=8,
        ).json()
        if "title" in resp:
            msg = f"**{resp['title']}**\n\n{resp.get('extract', 'No summary available.')}"
            return [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=resp["title"],
                    description=resp.get("extract", "")[:100],
                    input_message_content=InputTextMessageContent(msg),
                )
            ]
        return [_error_article("No Wikipedia article found for: " + text)]
    except Exception as e:
        return [_error_article(str(e))]


def pokedex_results(pokemon: str) -> list:
    try:
        resp = requests.get(
            f"https://some-random-api.ml/pokedex?pokemon={pokemon}", timeout=8
        ).json()
        caption = (
            f"**Pokemon:** `{resp['name']}`\n"
            f"**Pokedex:** `{resp['id']}`\n"
            f"**Type:** `{resp['type']}`\n"
            f"**Abilities:** `{resp['abilities']}`\n"
            f"**Height:** `{resp['height']}`\n"
            f"**Weight:** `{resp['weight']}`\n"
            f"**Gender:** `{resp['gender']}`\n"
            f"**Description:** `{resp['description']}`"
        )
        return [
            InlineQueryResultPhoto(
                id=str(uuid4()),
                title=resp["name"],
                description=resp.get("description", "")[:100],
                photo_url=f"https://img.pokemondb.net/artwork/large/{pokemon}.jpg",
                thumb_url=f"https://img.pokemondb.net/artwork/large/{pokemon}.jpg",
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
            )
        ]
    except Exception as e:
        return [_error_article(str(e))]


def ping_results() -> list:
    t1 = time.perf_counter()
    requests.get("https://api.telegram.org", timeout=5)
    t2 = time.perf_counter()
    ping_ms = round((t2 - t1) * 1000, 2)
    return [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"Ping: {ping_ms} ms",
            input_message_content=InputTextMessageContent(f"**Pong!** `{ping_ms} ms`"),
        )
    ]


def _error_article(msg: str) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=str(uuid4()),
        title="Error",
        description=msg[:100],
        input_message_content=InputTextMessageContent(msg),
    )


# ── Main inline handler ────────────────────────────────────────────────────────

def inline_query(update: Update, context: CallbackContext):
    query = update.inline_query.query.strip()
    results = []

    try:
        if not query:
            results = [alive_result(context)]

        elif query.startswith("tr "):
            # Format: tr <lang> <text>
            parts = query[3:].split(" ", 1)
            if len(parts) == 2:
                results = translate_results(parts[0], parts[1])
            else:
                results = [_error_article("Usage: tr <lang_code> <text>  e.g. tr hi Hello")]

        elif query.startswith("ud "):
            results = urban_results(query[3:])

        elif query.startswith("g "):
            results = google_results(query[2:])

        elif query.startswith("wall "):
            results = wall_results(query[5:])

        elif query.startswith("music "):
            results = saavn_results(query[6:])

        elif query.startswith("paste "):
            results = paste_results(query[6:])

        elif query.startswith("torrent "):
            results = torrent_results(query[8:])

        elif query.startswith("wiki "):
            results = wiki_results(query[5:])

        elif query.startswith("pokedex "):
            results = pokedex_results(query[8:])

        elif query == "ping":
            results = ping_results()

        elif query == "alive":
            results = [alive_result(context)]

        else:
            # Default: show help
            username = _get_bot_username(context)
            help_text = (
                "**Inline Commands:**\n"
                "`tr <lang> <text>` — Translate\n"
                "`ud <word>` — Urban Dictionary\n"
                "`g <query>` — Google Search\n"
                "`wall <query>` — Wallpapers\n"
                "`music <song>` — Music Search\n"
                "`paste <text>` — Paste text\n"
                "`torrent <name>` — Torrent Search\n"
                "`wiki <query>` — Wikipedia\n"
                "`pokedex <pokemon>` — Pokédex\n"
                "`ping` — Ping\n"
                "`alive` — Bot Status"
            )
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Go Inline", switch_inline_query_current_chat=""),
                    InlineKeyboardButton("Bot", url=f"https://t.me/{username}"),
                ]
            ])
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title="Inline Help",
                    description="Click to see all inline commands",
                    input_message_content=InputTextMessageContent(help_text),
                    reply_markup=buttons,
                )
            ]
    except Exception as e:
        results = [_error_article(f"Internal error: {e}")]

    update.inline_query.answer(results, cache_time=5)


INLINE_HANDLER = InlineQueryHandler(inline_query, run_async=True)
dispatcher.add_handler(INLINE_HANDLER)

__mod_name__ = "Inline"
__handlers__ = [INLINE_HANDLER]
