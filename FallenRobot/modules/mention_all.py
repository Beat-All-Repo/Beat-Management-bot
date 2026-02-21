import asyncio

from telethon import events
from telethon.errors import UserNotParticipantError
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator

from FallenRobot import telethn

spam_chats = []


@telethn.on(
    events.NewMessage(
        pattern=r"^(/tagall|/call|/tall|/all|/mentionall|#all|@all|@mentionall|@tagall|@utag)(.*)",
        func=lambda e: not e.is_private,
    )
)
async def all_mentions(event):
    chat_id = event.chat_id

    # Check if sender is admin
    is_admin = False
    try:
        partici_ = await telethn(GetParticipantRequest(event.chat_id, event.sender_id))
        if isinstance(
            partici_.participant, (ChannelParticipantAdmin, ChannelParticipantCreator)
        ):
            is_admin = True
    except UserNotParticipantError:
        is_admin = False
    except Exception:
        is_admin = False

    if not is_admin:
        return await event.respond("» Only admins can use this command!")

    extra_text = event.pattern_match.group(2).strip()

    if extra_text and event.is_reply:
        return await event.respond("» Give me ONE argument - either reply to a message OR provide text, not both!")

    if extra_text:
        mode = "text_on_cmd"
        msg = extra_text
    elif event.is_reply:
        mode = "text_on_reply"
        msg = await event.get_reply_message()
        if msg is None:
            return await event.respond(
                "» I can't mention members for older messages!"
            )
    else:
        return await event.respond(
            "» Reply to a message OR give me some text to mention others."
        )

    spam_chats.append(chat_id)
    usrnum = 0
    usrtxt = ""

    async for usr in telethn.iter_participants(chat_id):
        if chat_id not in spam_chats:
            break
        if usr.bot:
            continue
        usrnum += 1
        usrtxt += f"[{usr.first_name}](tg://user?id={usr.id}) "

        if usrnum == 10:
            if mode == "text_on_cmd":
                txt = f"{usrtxt}\n\n{msg}"
                await telethn.send_message(chat_id, txt)
            elif mode == "text_on_reply":
                await msg.reply(usrtxt)
            await asyncio.sleep(2)
            usrnum = 0
            usrtxt = ""

    # Send leftover mentions
    if usrtxt:
        if mode == "text_on_cmd":
            await telethn.send_message(chat_id, f"{usrtxt}\n\n{msg}")
        elif mode == "text_on_reply":
            await msg.reply(usrtxt)

    try:
        spam_chats.remove(chat_id)
    except ValueError:
        pass


@telethn.on(events.NewMessage(pattern=r"^/cancel$"))
async def cancel_spam(event):
    if event.chat_id not in spam_chats:
        return await event.respond("» There is no ongoing mention process.")
    try:
        spam_chats.remove(event.chat_id)
    except ValueError:
        pass
    return await event.respond("» Mentioning stopped!")


__mod_name__ = "Mention All"
