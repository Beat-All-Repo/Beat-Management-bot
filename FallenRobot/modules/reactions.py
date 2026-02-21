import requests
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from FallenRobot import dispatcher
from FallenRobot.modules.disable import DisableAbleCommandHandler

NEKOS_API = "https://nekos.best/api/v2/{}"


def _send_reaction(update: Update, action: str, verb: str, emoji: str):
    message = update.effective_message
    sender = update.effective_user.first_name

    try:
        data = requests.get(NEKOS_API.format(action), timeout=10).json()
        gif_url = data["results"][0]["url"]
        artist_name = data["results"][0].get("artist_name", "Unknown")
        anime_name = data["results"][0].get("anime_name", "Unknown")
    except Exception:
        message.reply_text("Couldn't fetch a GIF right now. Try again later!")
        return

    if message.reply_to_message:
        target = message.reply_to_message.from_user.first_name
        caption = f"{emoji} *{sender}* {verb} *{target}*!\n_From: {anime_name}_"
    else:
        caption = f"{emoji} *{sender}* wants to {action} someone!\n_From: {anime_name}_"

    message.reply_animation(
        animation=gif_url,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
    )


def hug(update: Update, context: CallbackContext):
    _send_reaction(update, "hug", "hugs", "🤗")


def pat(update: Update, context: CallbackContext):
    _send_reaction(update, "pat", "pats", "👋")


def slap(update: Update, context: CallbackContext):
    _send_reaction(update, "slap", "slaps", "👋")


def kiss(update: Update, context: CallbackContext):
    _send_reaction(update, "kiss", "kisses", "💋")


def poke(update: Update, context: CallbackContext):
    _send_reaction(update, "poke", "pokes", "👉")


def wave(update: Update, context: CallbackContext):
    _send_reaction(update, "wave", "waves at", "👋")


def bite(update: Update, context: CallbackContext):
    _send_reaction(update, "bite", "bites", "😬")


def punch(update: Update, context: CallbackContext):
    _send_reaction(update, "punch", "punches", "👊")


def nod(update: Update, context: CallbackContext):
    _send_reaction(update, "nod", "nods at", "🙂")


def shoot(update: Update, context: CallbackContext):
    _send_reaction(update, "shoot", "shoots", "🔫")


def wink(update: Update, context: CallbackContext):
    _send_reaction(update, "wink", "winks at", "😉")


def cry(update: Update, context: CallbackContext):
    _send_reaction(update, "cry", "is crying", "😢")


def laugh(update: Update, context: CallbackContext):
    _send_reaction(update, "laugh", "is laughing at", "😂")


def blush(update: Update, context: CallbackContext):
    _send_reaction(update, "blush", "blushes at", "😊")


__help__ = """
*Anime Reactions:*
Send fun anime GIFs to interact with others!

 • `/hug`*:* hug someone
 • `/pat`*:* pat someone
 • `/slap`*:* slap someone
 • `/kiss`*:* kiss someone
 • `/poke`*:* poke someone
 • `/wave`*:* wave at someone
 • `/bite`*:* bite someone
 • `/punch`*:* punch someone
 • `/wink`*:* wink at someone
 • `/cry`*:* cry
 • `/laugh`*:* laugh
 • `/blush`*:* blush

_Reply to a user's message to target them!_
"""

HUG_HANDLER = DisableAbleCommandHandler("hug", hug, run_async=True)
PAT_HANDLER = DisableAbleCommandHandler("pat", pat, run_async=True)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, run_async=True)
KISS_HANDLER = DisableAbleCommandHandler("kiss", kiss, run_async=True)
POKE_HANDLER = DisableAbleCommandHandler("poke", poke, run_async=True)
WAVE_HANDLER = DisableAbleCommandHandler("wave", wave, run_async=True)
BITE_HANDLER = DisableAbleCommandHandler("bite", bite, run_async=True)
PUNCH_HANDLER = DisableAbleCommandHandler("punch", punch, run_async=True)
NOD_HANDLER = DisableAbleCommandHandler("nod", nod, run_async=True)
SHOOT_HANDLER = DisableAbleCommandHandler("shoot", shoot, run_async=True)
WINK_HANDLER = DisableAbleCommandHandler("wink", wink, run_async=True)
CRY_HANDLER = DisableAbleCommandHandler("cry", cry, run_async=True)
LAUGH_HANDLER = DisableAbleCommandHandler("laugh", laugh, run_async=True)
BLUSH_HANDLER = DisableAbleCommandHandler("blush", blush, run_async=True)

dispatcher.add_handler(HUG_HANDLER)
dispatcher.add_handler(PAT_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(KISS_HANDLER)
dispatcher.add_handler(POKE_HANDLER)
dispatcher.add_handler(WAVE_HANDLER)
dispatcher.add_handler(BITE_HANDLER)
dispatcher.add_handler(PUNCH_HANDLER)
dispatcher.add_handler(NOD_HANDLER)
dispatcher.add_handler(SHOOT_HANDLER)
dispatcher.add_handler(WINK_HANDLER)
dispatcher.add_handler(CRY_HANDLER)
dispatcher.add_handler(LAUGH_HANDLER)
dispatcher.add_handler(BLUSH_HANDLER)

__mod_name__ = "Reactions"
__command_list__ = [
    "hug", "pat", "slap", "kiss", "poke",
    "wave", "bite", "punch", "nod", "shoot",
    "wink", "cry", "laugh", "blush",
]
__handlers__ = [
    HUG_HANDLER, PAT_HANDLER, SLAP_HANDLER, KISS_HANDLER, POKE_HANDLER,
    WAVE_HANDLER, BITE_HANDLER, PUNCH_HANDLER, NOD_HANDLER, SHOOT_HANDLER,
    WINK_HANDLER, CRY_HANDLER, LAUGH_HANDLER, BLUSH_HANDLER,
]
