"""
Anime Request System for FallenRobot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SPAM PROTECTION LAYERS:
  1. AniList API validation — only real anime titles accepted
  2. Per-user cooldown (5 min between requests)
  3. Per-user pending cap (max 5 pending at a time)
  4. Duplicate detection (same title can't be requested twice in same chat)

USER COMMANDS:
  /request <anime name>  — submit a validated anime request
  /myrequests            — view your own requests

ADMIN COMMANDS:
  /requests              — view all pending requests
  /fulfill <id>          — mark a request as fulfilled
  /delrequest <id>       — delete a request
"""

import threading
import time

import requests as http
from sqlalchemy import BigInteger, Boolean, Column, String, UnicodeText
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from FallenRobot import dispatcher, DRAGONS
from FallenRobot.modules.disable import DisableAbleCommandHandler
from FallenRobot.modules.sql import BASE, SESSION

# ── Tunable constants ──────────────────────────────────────────────────────────
COOLDOWN_SECONDS = 300       # seconds a user must wait between requests
MAX_PENDING_PER_USER = 5     # max unresolved requests a user may have at once

ANILIST_API = "https://graphql.anilist.co"
ANILIST_QUERY = """
query ($search: String) {
  Media(search: $search, type: ANIME) {
    id
    title { romaji english native }
    status
    episodes
    averageScore
    siteUrl
  }
}
"""

# ── In-memory cooldown {user_id: unix_timestamp_of_last_request} ───────────────
_cooldowns: dict = {}
_cd_lock = threading.Lock()


# ── SQL model ──────────────────────────────────────────────────────────────────

class AnimeRequest(BASE):
    __tablename__ = "anime_requests"

    id             = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id        = Column(BigInteger,  nullable=False, index=True)
    chat_id        = Column(String(14),  nullable=False, index=True)
    raw_query      = Column(UnicodeText, nullable=False)          # exactly what user typed
    validated_title = Column(UnicodeText, nullable=False)         # canonical title from AniList
    anilist_id     = Column(BigInteger,  nullable=True)           # AniList media ID
    anilist_url    = Column(UnicodeText, nullable=True)
    fulfilled      = Column(Boolean,     default=False)
    created_at     = Column(BigInteger,  nullable=False)

    def __init__(self, user_id, chat_id, raw_query, validated_title,
                 anilist_id=None, anilist_url=""):
        self.user_id         = user_id
        self.chat_id         = str(chat_id)
        self.raw_query       = raw_query
        self.validated_title = validated_title
        self.anilist_id      = anilist_id
        self.anilist_url     = anilist_url
        self.fulfilled       = False
        self.created_at      = int(time.time())

    def __repr__(self):
        return f"<AnimeRequest #{self.id} — {self.validated_title}>"


AnimeRequest.__table__.create(checkfirst=True)
DB_LOCK = threading.RLock()


# ── AniList validation ─────────────────────────────────────────────────────────

def validate_on_anilist(query: str) -> dict | None:
    """
    Hit AniList GraphQL and return media info if found, else None.
    A None return means the title is NOT a real/known anime — request rejected.
    """
    try:
        resp = http.post(
            ANILIST_API,
            json={"query": ANILIST_QUERY, "variables": {"search": query}},
            timeout=8,
        )
        data = resp.json()

        if "errors" in data or not data.get("data", {}).get("Media"):
            return None

        media = data["data"]["Media"]
        titles = media["title"]
        return {
            "id":       media["id"],
            "romaji":   titles.get("romaji") or "",
            "english":  titles.get("english") or "",
            "native":   titles.get("native") or "",
            "status":   (media.get("status") or "").replace("_", " ").title(),
            "episodes": media.get("episodes") or "?",
            "score":    media.get("averageScore") or "N/A",
            "url":      media.get("siteUrl") or "",
        }
    except Exception:
        return None


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _insert_request(user_id, chat_id, raw_query,
                    validated_title, anilist_id, anilist_url) -> int:
    with DB_LOCK:
        row = AnimeRequest(user_id, str(chat_id), raw_query,
                           validated_title, anilist_id, anilist_url)
        SESSION.add(row)
        SESSION.commit()
        return row.id


def _pending_count_for_user(user_id: int, chat_id) -> int:
    try:
        return (SESSION.query(AnimeRequest)
                .filter_by(user_id=user_id, chat_id=str(chat_id), fulfilled=False)
                .count())
    finally:
        SESSION.close()


def _duplicate_exists(chat_id, anilist_id: int) -> bool:
    """True if this AniList title is already pending in this chat."""
    try:
        return (SESSION.query(AnimeRequest)
                .filter_by(chat_id=str(chat_id),
                           anilist_id=anilist_id,
                           fulfilled=False)
                .count()) > 0
    finally:
        SESSION.close()


def _get_pending(chat_id) -> list:
    try:
        return (SESSION.query(AnimeRequest)
                .filter_by(chat_id=str(chat_id), fulfilled=False)
                .order_by(AnimeRequest.id.asc()).all())
    finally:
        SESSION.close()


def _fulfill(req_id: int) -> bool:
    with DB_LOCK:
        row = SESSION.query(AnimeRequest).get(req_id)
        if row:
            row.fulfilled = True
            SESSION.commit()
            return True
        SESSION.close()
        return False


def _delete(req_id: int) -> bool:
    with DB_LOCK:
        row = SESSION.query(AnimeRequest).get(req_id)
        if row:
            SESSION.delete(row)
            SESSION.commit()
            return True
        SESSION.close()
        return False


# ── Cooldown helpers ───────────────────────────────────────────────────────────

def _cooldown_remaining(user_id: int) -> int:
    with _cd_lock:
        elapsed = time.time() - _cooldowns.get(user_id, 0)
        remaining = COOLDOWN_SECONDS - elapsed
        return max(0, int(remaining))


def _stamp_cooldown(user_id: int):
    with _cd_lock:
        _cooldowns[user_id] = time.time()


# ── /request ───────────────────────────────────────────────────────────────────

def request_cmd(update: Update, context: CallbackContext):
    message = update.effective_message
    user    = update.effective_user
    chat    = update.effective_chat
    args    = context.args

    if not args:
        return message.reply_text(
            "📋 *Usage:* `/request <anime name>`\n"
            "_Example:_ `/request Attack on Titan`",
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── layer 1: cooldown ──────────────────────────────────────────────────────
    wait = _cooldown_remaining(user.id)
    if wait:
        m, s = divmod(wait, 60)
        return message.reply_text(
            f"⏳ Slow down! Wait *{m}m {s}s* before your next request.",
            parse_mode=ParseMode.MARKDOWN,
        )

    # ── layer 2: pending cap ───────────────────────────────────────────────────
    pending = _pending_count_for_user(user.id, chat.id)
    if pending >= MAX_PENDING_PER_USER:
        return message.reply_text(
            f"❌ You already have *{pending}* unresolved requests.\n"
            "Please wait for them to be fulfilled first.",
            parse_mode=ParseMode.MARKDOWN,
        )

    query = " ".join(args).strip()

    # ── layer 3: AniList validation ────────────────────────────────────────────
    wait_msg = message.reply_text(
        f"🔍 Checking *{query}* on AniList...",
        parse_mode=ParseMode.MARKDOWN,
    )

    anime = validate_on_anilist(query)

    if not anime:
        wait_msg.edit_text(
            f"❌ *\"{query}\"* is not recognised as a valid anime.\n\n"
            "Only real anime titles (verified via AniList) are accepted "
            "to keep the request list spam-free.\n\n"
            "_Tip:_ find the exact title on [AniList](https://anilist.co) first.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
        return

    # ── layer 4: duplicate detection ──────────────────────────────────────────
    if _duplicate_exists(chat.id, anime["id"]):
        wait_msg.edit_text(
            f"⚠️ *{anime['english'] or anime['romaji']}* is already in the pending request list!\n"
            "No need to request it again.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # ── all checks passed — save ───────────────────────────────────────────────
    canonical = anime["english"] or anime["romaji"]
    req_id = _insert_request(
        user.id, chat.id, query,
        canonical, anime["id"], anime["url"]
    )
    _stamp_cooldown(user.id)

    wait_msg.delete()

    message.reply_text(
        f"✅ *Request Submitted!*\n\n"
        f"🎬 *Anime:* [{canonical}]({anime['url']})\n"
        f"   _({anime['native']})_\n"
        f"📺 *Episodes:* `{anime['episodes']}`\n"
        f"📊 *Status:* `{anime['status']}`\n"
        f"⭐ *Score:* `{anime['score']}/100`\n\n"
        f"🔖 *Request ID:* `#{req_id}`\n"
        f"_Admins will review it soon._",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False,
    )


# ── /myrequests ────────────────────────────────────────────────────────────────

def myrequests_cmd(update: Update, context: CallbackContext):
    message = update.effective_message
    user    = update.effective_user
    chat    = update.effective_chat

    try:
        rows = (SESSION.query(AnimeRequest)
                .filter_by(user_id=user.id, chat_id=str(chat.id))
                .order_by(AnimeRequest.fulfilled.asc(), AnimeRequest.id.desc())
                .limit(10).all())
    finally:
        SESSION.close()

    if not rows:
        return message.reply_text("You have no requests in this chat yet.")

    lines = ["📋 *Your Requests:*\n"]
    for r in rows:
        icon = "✅" if r.fulfilled else "⏳"
        lines.append(
            f"{icon} `#{r.id}` — [{r.validated_title}]({r.anilist_url})"
        )

    message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ── /requests (admin) ──────────────────────────────────────────────────────────

def requests_list_cmd(update: Update, context: CallbackContext):
    message = update.effective_message
    user    = update.effective_user
    chat    = update.effective_chat

    member = chat.get_member(user.id)
    if member.status not in ("administrator", "creator") and user.id not in DRAGONS:
        return message.reply_text("» Only admins can view the request list!")

    pending = _get_pending(chat.id)
    if not pending:
        return message.reply_text("✨ No pending requests right now!")

    lines = [f"📋 *Pending Requests — {chat.title}:*\n"]
    for r in pending:
        lines.append(
            f"• `#{r.id}` — [{r.validated_title}]({r.anilist_url})\n"
            f"   _user_ `{r.user_id}`"
        )
    lines.append("\n`/fulfill <id>` · `/delrequest <id>`")

    message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ── /fulfill (admin) ───────────────────────────────────────────────────────────

def fulfill_cmd(update: Update, context: CallbackContext):
    message = update.effective_message
    user    = update.effective_user
    chat    = update.effective_chat
    args    = context.args

    member = chat.get_member(user.id)
    if member.status not in ("administrator", "creator") and user.id not in DRAGONS:
        return message.reply_text("» Only admins can fulfill requests!")

    if not args or not args[0].isdigit():
        return message.reply_text(
            "Usage: `/fulfill <request id>`", parse_mode=ParseMode.MARKDOWN
        )

    req_id = int(args[0])
    if _fulfill(req_id):
        message.reply_text(
            f"✅ Request `#{req_id}` marked as *fulfilled*!",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        message.reply_text(
            f"❌ Request `#{req_id}` not found.",
            parse_mode=ParseMode.MARKDOWN,
        )


# ── /delrequest (admin) ────────────────────────────────────────────────────────

def delrequest_cmd(update: Update, context: CallbackContext):
    message = update.effective_message
    user    = update.effective_user
    chat    = update.effective_chat
    args    = context.args

    member = chat.get_member(user.id)
    if member.status not in ("administrator", "creator") and user.id not in DRAGONS:
        return message.reply_text("» Only admins can delete requests!")

    if not args or not args[0].isdigit():
        return message.reply_text(
            "Usage: `/delrequest <request id>`", parse_mode=ParseMode.MARKDOWN
        )

    req_id = int(args[0])
    if _delete(req_id):
        message.reply_text(
            f"🗑️ Request `#{req_id}` deleted.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        message.reply_text(
            f"❌ Request `#{req_id}` not found.",
            parse_mode=ParseMode.MARKDOWN,
        )


# ── Register handlers ──────────────────────────────────────────────────────────

REQ_HANDLER      = DisableAbleCommandHandler("request",      request_cmd,       run_async=True)
MYREQ_HANDLER    = DisableAbleCommandHandler("myrequests",   myrequests_cmd,    run_async=True)
LIST_HANDLER     = DisableAbleCommandHandler("requests",     requests_list_cmd, run_async=True)
FULFILL_HANDLER  = DisableAbleCommandHandler("fulfill",      fulfill_cmd,       run_async=True)
DELREQ_HANDLER   = DisableAbleCommandHandler("delrequest",   delrequest_cmd,    run_async=True)

for h in [REQ_HANDLER, MYREQ_HANDLER, LIST_HANDLER, FULFILL_HANDLER, DELREQ_HANDLER]:
    dispatcher.add_handler(h)

__mod_name__     = "Requests"
__command_list__ = ["request", "myrequests", "requests", "fulfill", "delrequest"]
__handlers__     = [REQ_HANDLER, MYREQ_HANDLER, LIST_HANDLER, FULFILL_HANDLER, DELREQ_HANDLER]
__help__ = """
*Anime Request System:*

*User commands:*
 • `/request <anime name>` — submit a request (must be a real AniList title)
 • `/myrequests` — see your own requests & status

*Admin commands:*
 • `/requests` — view all pending requests
 • `/fulfill <id>` — mark a request fulfilled
 • `/delrequest <id>` — delete a request

*Built-in spam protection:*
 ✦ AniList API validates every title before it touches the DB
 ✦ 5-minute cooldown between requests per user
 ✦ Max 5 pending requests per user at a time
 ✦ Duplicate titles (same chat) are rejected automatically
"""
