import random
import os

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from FallenRobot import dispatcher, SUPPORT_CHAT
from FallenRobot.modules import ALL_MODULES
from FallenRobot.modules.helper_funcs.misc import paginate_modules

# ── Configurable pictures ──────────────────────────────────────────────────────
HELP_PICS = [p.strip() for p in os.environ.get("HELP_PICS", "").split(",") if p.strip()]
if not HELP_PICS:
    HELP_PICS = ["https://ibb.co/BVccVQZq"]

START_PICS = [p.strip() for p in os.environ.get("START_PICS", "").split(",") if p.strip()]
if not START_PICS:
    START_PICS = ["https://telegra.ph/file/ec17880d61180d3312d6a.jpg"]

# Channel / support links — update these to your own
ANIME_CHANNEL = os.environ.get("ANIME_CHANNEL", "https://t.me/Beat_Hindi_Dubbed")
CONTACT_ADMIN = os.environ.get("CONTACT_ADMIN", f"https://t.me/{SUPPORT_CHAT}")


def get_random_pic(lst: list) -> str:
    try:
        return random.choice(lst)
    except Exception:
        return lst[0]


# ── Imported by other modules to build per-module help ────────────────────────
IMPORTED = {}
HELPABLE = {}


def _load_modules():
    global IMPORTED, HELPABLE
    for module_name in ALL_MODULES:
        imported_module = __import__(
            "FallenRobot.modules." + module_name, fromlist=["FallenRobot.modules"]
        )
        if not hasattr(imported_module, "__mod_name__"):
            imported_module.__mod_name__ = module_name

        if imported_module.__mod_name__.lower() not in IMPORTED:
            IMPORTED[imported_module.__mod_name__.lower()] = imported_module
        else:
            raise Exception(
                "Can't have two modules with the same name! Please fix this."
            )

        if hasattr(imported_module, "__help__") and imported_module.__help__:
            HELPABLE[imported_module.__mod_name__.lower()] = imported_module


_load_modules()


# ── /start ─────────────────────────────────────────────────────────────────────
def start(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user

    start_text = (
        f"<b>Hello {user.first_name}! 👋</b>\n\n"
        "<b>➪ I am a powerful group management & anime bot.</b>\n\n"
        "<blockquote expandable>"
        "I can help you manage your group with features like:\n"
        "• Admin tools (promote, demote, ban, mute)\n"
        "• Anime info, quotes & reactions\n"
        "• Welcome messages, notes, filters\n"
        "• Inline search & much more!\n\n"
        "Use /help to see all available commands."
        "</blockquote>"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Help", callback_data="help_back"),
            InlineKeyboardButton("📢 Channel", url=ANIME_CHANNEL),
        ],
        [
            InlineKeyboardButton("👤 Contact Admin", url=CONTACT_ADMIN),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ])

    pic = get_random_pic(START_PICS)
    try:
        message.reply_photo(
            photo=pic,
            caption=start_text,
            parse_mode=ParseMode.HTML,
            reply_markup=buttons,
        )
    except Exception:
        message.reply_text(
            start_text,
            parse_mode=ParseMode.HTML,
            reply_markup=buttons,
        )


# ── /help ──────────────────────────────────────────────────────────────────────
def help_command(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user

    help_text = (
        f"<b>‼️ Hello {user.first_name}!</b>\n\n"
        "<blockquote expandable>"
        "<b>➪ I am a private file sharing & group management bot.\n\n"
        "➪ In order to get files you have to join all mentioned channels.\n\n"
        "➪ Use the buttons below to browse all my commands.</b>"
        "</blockquote>\n"
        "<b>◈ Still have doubts? Contact admin below!</b>"
    )

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Anime Channel", url=ANIME_CHANNEL),
            InlineKeyboardButton("👤 Contact Admin", url=CONTACT_ADMIN),
        ],
        [
            InlineKeyboardButton("📖 Commands", callback_data="help_back"),
            InlineKeyboardButton("❌ Close", callback_data="close"),
        ],
    ])

    pic = get_random_pic(HELP_PICS)
    try:
        message.reply_photo(
            photo=pic,
            caption=help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=buttons,
        )
    except Exception:
        message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=buttons,
        )


# ── Callback: module list / back ───────────────────────────────────────────────
def help_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "help_back":
        query.message.edit_text(
            text="<b>📖 Choose a module to see help:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, HELPABLE, "help")
            ),
        )

    elif query.data.startswith("help_module("):
        mod_name = query.data.split("help_module(")[1][:-1]
        module = HELPABLE.get(mod_name)
        if module:
            back_btn = InlineKeyboardMarkup(
                [[InlineKeyboardButton("◀ Back", callback_data="help_back")]]
            )
            query.message.edit_text(
                text=f"<b>Help for {module.__mod_name__}:</b>\n{module.__help__}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_btn,
                disable_web_page_preview=True,
            )

    elif query.data.startswith("help_prev("):
        page = int(query.data.split("help_prev(")[1][:-1])
        query.message.edit_text(
            text="<b>📖 Choose a module to see help:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(page, HELPABLE, "help")
            ),
        )

    elif query.data.startswith("help_next("):
        page = int(query.data.split("help_next(")[1][:-1])
        query.message.edit_text(
            text="<b>📖 Choose a module to see help:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(page, HELPABLE, "help")
            ),
        )

    elif query.data == "close":
        query.message.delete()


# ── Register handlers ──────────────────────────────────────────────────────────
START_HANDLER = CommandHandler("start", start, run_async=True)
HELP_HANDLER = CommandHandler("help", help_command, run_async=True)
HELP_CALLBACK_HANDLER = CallbackQueryHandler(
    help_button,
    pattern=r"^(help_.*|close)$",
    run_async=True,
)

dispatcher.add_handler(START_HANDLER)
dispatcher.add_handler(HELP_HANDLER)
dispatcher.add_handler(HELP_CALLBACK_HANDLER)

__mod_name__ = "Help"
__handlers__ = [START_HANDLER, HELP_HANDLER, HELP_CALLBACK_HANDLER]
