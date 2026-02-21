import threading

from sqlalchemy import BigInteger, Column, String, UnicodeText, Boolean
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler

from FallenRobot import dispatcher, DRAGONS
from FallenRobot.modules.disable import DisableAbleCommandHandler
from FallenRobot.modules.sql import BASE, SESSION

# ── SQL Model ──────────────────────────────────────────────────────────────────

class AnimeRequest(BASE):
    __tablename__ = "anime_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(String(14), nullable=False)
    request = Column(UnicodeText, nullable=False)
    fulfilled = Column(Boolean, default=False)

    def __init__(self, user_id, chat_id, request):
        self.user_id = user_id
        self.chat_id = str(chat_id)
        self.request = request
        self.fulfilled = False

    def __repr__(self):
        return f"<Request {self.id} by {self.user_id}>"


AnimeRequest.__table__.create(checkfirst=True)
REQUEST_LOCK = threading.RLock()


# ── SQL helpers ────────────────────────────────────────────────────────────────

def add_request(user_id, chat_id, request_text):
    with REQUEST_LOCK:
        req = AnimeRequest(user_id, str(chat_id), request_text)
        SESSION.add(req)
        SESSION.commit()
        return req.id


def get_all_requests(chat_id, only_pending=True):
    try:
        q = SESSION.query(AnimeRequest).filter(
            AnimeRequest.chat_id == str(chat_id)
        )
        if only_pending:
            q = q.filter(AnimeRequest.fulfilled == False)
        return q.order_by(AnimeRequest.id.asc()).all()
    finally:
        SESSION.close()


def fulfill_request(request_id):
    with REQUEST_LOCK:
        req = SESSION.query(AnimeRequest).get(request_id)
        if req:
            req.fulfilled = True
            SESSION.commit()
            return True
        SESSION.close()
        return False


def delete_request(request_id):
    with REQUEST_LOCK:
        req = SESSION.query(AnimeRequest).get(request_id)
        if req:
            SESSION.delete(req)
            SESSION.commit()
            return True
        SESSION.close()
        return False


# ── Handlers ───────────────────────────────────────────────────────────────────

def request(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    args = context.args

    if not args:
        message.reply_text(
            "Please specify what you want to request.\n"
            "Usage: `/request <anime/movie name>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    request_text = " ".join(args)
    req_id = add_request(user.id, chat.id, request_text)

    message.reply_text(
        f"✅ Your request has been submitted!\n\n"
        f"📋 *Request ID:* `#{req_id}`\n"
        f"🎬 *Requested:* `{request_text}`\n\n"
        f"Admins will review your request soon.",
        parse_mode=ParseMode.MARKDOWN,
    )


def requests_list(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    # Only admins/dragons can view all requests
    member = chat.get_member(user.id)
    if not (
        member.status in ("administrator", "creator")
        or user.id in DRAGONS
    ):
        message.reply_text("» Only admins can view the requests list!")
        return

    pending = get_all_requests(chat.id, only_pending=True)

    if not pending:
        message.reply_text("✨ No pending requests right now!")
        return

    text = f"📋 *Pending Requests in {chat.title}:*\n\n"
    for req in pending:
        text += f"• `#{req.id}` — {req.request} _(by user `{req.user_id}`)_\n"

    text += "\nUse `/fulfill <id>` to mark a request as done.\nUse `/delrequest <id>` to delete a request."
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def fulfill(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    args = context.args

    member = chat.get_member(user.id)
    if not (
        member.status in ("administrator", "creator")
        or user.id in DRAGONS
    ):
        message.reply_text("» Only admins can fulfill requests!")
        return

    if not args or not args[0].isdigit():
        message.reply_text("Usage: `/fulfill <request id>`", parse_mode=ParseMode.MARKDOWN)
        return

    req_id = int(args[0])
    if fulfill_request(req_id):
        message.reply_text(
            f"✅ Request `#{req_id}` has been marked as fulfilled!",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        message.reply_text(f"❌ Request `#{req_id}` not found.", parse_mode=ParseMode.MARKDOWN)


def delrequest(update: Update, context: CallbackContext):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    args = context.args

    member = chat.get_member(user.id)
    if not (
        member.status in ("administrator", "creator")
        or user.id in DRAGONS
    ):
        message.reply_text("» Only admins can delete requests!")
        return

    if not args or not args[0].isdigit():
        message.reply_text("Usage: `/delrequest <request id>`", parse_mode=ParseMode.MARKDOWN)
        return

    req_id = int(args[0])
    if delete_request(req_id):
        message.reply_text(
            f"🗑️ Request `#{req_id}` has been deleted.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        message.reply_text(f"❌ Request `#{req_id}` not found.", parse_mode=ParseMode.MARKDOWN)


__help__ = """
*Anime/Movie Request System:*

*User Commands:*
 • `/request <name>`*:* submit a request for an anime or movie

*Admin Commands:*
 • `/requests`*:* view all pending requests
 • `/fulfill <id>`*:* mark a request as fulfilled
 • `/delrequest <id>`*:* delete a request
"""

REQUEST_HANDLER = DisableAbleCommandHandler("request", request, run_async=True)
REQUESTS_LIST_HANDLER = DisableAbleCommandHandler("requests", requests_list, run_async=True)
FULFILL_HANDLER = DisableAbleCommandHandler("fulfill", fulfill, run_async=True)
DELREQUEST_HANDLER = DisableAbleCommandHandler("delrequest", delrequest, run_async=True)

dispatcher.add_handler(REQUEST_HANDLER)
dispatcher.add_handler(REQUESTS_LIST_HANDLER)
dispatcher.add_handler(FULFILL_HANDLER)
dispatcher.add_handler(DELREQUEST_HANDLER)

__mod_name__ = "Requests"
__command_list__ = ["request", "requests", "fulfill", "delrequest"]
__handlers__ = [
    REQUEST_HANDLER,
    REQUESTS_LIST_HANDLER,
    FULFILL_HANDLER,
    DELREQUEST_HANDLER,
]
