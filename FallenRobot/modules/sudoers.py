import os
import time

import psutil
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

import FallenRobot.modules.sql.users_sql as sql
from FallenRobot import dispatcher, StartTime, DEV_USERS, DRAGONS
from FallenRobot.modules.helper_funcs.chat_status import dev_plus
from FallenRobot.modules.disable import DisableAbleCommandHandler


def get_readable_time(seconds: int) -> str:
    result = ""
    (days, remainder) = divmod(seconds, 86400)
    (hours, remainder) = divmod(remainder, 3600)
    (minutes, second) = divmod(remainder, 60)
    if days != 0:
        result += f"{days}d "
    if hours != 0:
        result += f"{hours}h "
    if minutes != 0:
        result += f"{minutes}m "
    result += f"{second}s"
    return result


def get_bot_stats() -> str:
    bot_uptime = int(time.time() - StartTime)
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    process = psutil.Process(os.getpid())
    bot_ram = round(process.memory_info()[0] / 1024 ** 2)

    try:
        users = sql.num_users()
        chats = sql.num_chats()
    except Exception:
        users = "N/A"
        chats = "N/A"

    stats = (
        f"<b>⚙️ System Stats</b>\n\n"
        f"<b>• Uptime:</b> <code>{get_readable_time(bot_uptime)}</code>\n"
        f"<b>• Bot RAM:</b> <code>{bot_ram} MB</code>\n"
        f"<b>• CPU:</b> <code>{cpu}%</code>\n"
        f"<b>• RAM:</b> <code>{mem}%</code>\n"
        f"<b>• Disk:</b> <code>{disk}%</code>\n"
        f"<b>• Chats:</b> <code>{chats}</code>\n"
        f"<b>• Users:</b> <code>{users}</code>"
    )
    return stats


@dev_plus
def stats(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
        get_bot_stats(),
        parse_mode=ParseMode.HTML,
    )


@dev_plus
def ping(update: Update, context: CallbackContext):
    msg = update.effective_message
    t1 = time.perf_counter()
    message = msg.reply_text("Pinging...")
    t2 = time.perf_counter()
    message.edit_text(
        f"<b>🏓 Pong!</b>\n<code>{round((t2 - t1) * 1000, 2)} ms</code>",
        parse_mode=ParseMode.HTML,
    )


STATS_HANDLER = DisableAbleCommandHandler(["stats", "botstats"], stats, run_async=True)
PING_HANDLER = DisableAbleCommandHandler("ping", ping, run_async=True)

dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(PING_HANDLER)

__mod_name__ = "Sᴜᴅᴏᴇʀs"
__command_list__ = ["stats", "ping"]
__handlers__ = [STATS_HANDLER, PING_HANDLER]
