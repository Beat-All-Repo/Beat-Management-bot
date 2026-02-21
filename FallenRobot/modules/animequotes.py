import requests
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from FallenRobot import dispatcher
from FallenRobot.modules.disable import DisableAbleCommandHandler

ANIMECHAN_API = "https://animechan.io/api/v1/quotes/random"


def animequote(update: Update, context: CallbackContext):
    message = update.effective_message

    try:
        response = requests.get(ANIMECHAN_API, timeout=10).json()
        data = response.get("data", {})
        quote = data.get("content", "No quote found.")
        character = data.get("character", {}).get("name", "Unknown")
        anime = data.get("anime", {}).get("name", "Unknown")
    except Exception:
        message.reply_text("Couldn't fetch a quote right now. Try again later!")
        return

    msg = (
        f"💬 *\"{quote}\"*\n\n"
        f"— *{character}*\n"
        f"📺 _{anime}_"
    )
    message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


__help__ = """
*Anime Quotes:*

 • `/aq`*:* get a random anime quote
 • `/animequote`*:* same as /aq
"""

AQ_HANDLER = DisableAbleCommandHandler(["aq", "animequote"], animequote, run_async=True)

dispatcher.add_handler(AQ_HANDLER)

__mod_name__ = "AnimeQuotes"
__command_list__ = ["aq", "animequote"]
__handlers__ = [AQ_HANDLER]
