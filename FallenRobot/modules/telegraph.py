import os

from PIL import Image
from telegraph import Telegraph, exceptions, upload_file

from FallenRobot import telethn
from telethon import events
from telethon.tl import types


TMP_DOWNLOAD_DIRECTORY = "tg-File/"
os.makedirs(TMP_DOWNLOAD_DIRECTORY, exist_ok=True)

telegraph = Telegraph()
data = telegraph.create_account(short_name="FallenRobot")
auth_url = data["auth_url"]


@telethn.on(events.NewMessage(pattern=r"^/t(gm|gt) ?(.*)"))
async def telegrap(event):
    optional_title = event.pattern_match.group(2)
    if not event.reply_to_msg_id:
        return await event.reply("Reply to a message to get a permanent telegra.ph link.")

    reply_msg = await event.get_reply_message()
    input_str = event.pattern_match.group(1)

    if input_str == "gm":
        downloaded_file_name = await telethn.download_media(
            reply_msg, TMP_DOWNLOAD_DIRECTORY
        )
        if not downloaded_file_name:
            await telethn.send_message(event.chat_id, "Not Supported Format Media!")
            return
        if downloaded_file_name.endswith(".webp"):
            resize_image(downloaded_file_name)
        try:
            media_urls = upload_file(downloaded_file_name)
        except exceptions.TelegraphException as exc:
            await event.reply(f"ERROR: {str(exc)}")
        else:
            await telethn.send_message(
                event.chat_id,
                "✅ Successfully uploaded to Telegraph!",
                buttons=[
                    [
                        types.KeyboardButtonUrl(
                            "➡ View Telegraph",
                            f"https://te.legra.ph{media_urls[0]}",
                        )
                    ]
                ],
            )
        finally:
            if os.path.isfile(downloaded_file_name):
                os.remove(downloaded_file_name)

    elif input_str == "gt":
        user_object = await telethn.get_entity(reply_msg.sender_id)
        title_of_page = optional_title or user_object.first_name
        page_content = reply_msg.message or ""

        if reply_msg.media and not page_content:
            await telethn.send_message(event.chat_id, "Not Supported Format Text!")
            return

        if reply_msg.media:
            downloaded_file_name = await telethn.download_media(
                reply_msg, TMP_DOWNLOAD_DIRECTORY
            )
            if downloaded_file_name:
                m_list = []
                with open(downloaded_file_name, "rb") as fd:
                    m_list = fd.readlines()
                for m in m_list:
                    page_content += m.decode("UTF-8") + "\n"
                os.remove(downloaded_file_name)

        page_content = page_content.replace("\n", "<br>")
        try:
            response = telegraph.create_page(
                title=title_of_page,
                html_content=page_content,
            )
            page_url = f"https://telegra.ph/{response['path']}"
            await telethn.send_message(
                event.chat_id,
                "✅ Successfully uploaded to Telegraph!",
                buttons=[
                    [
                        types.KeyboardButtonUrl(
                            "➡ View Telegraph",
                            page_url,
                        )
                    ]
                ],
            )
        except Exception as e:
            await event.reply(f"Error creating Telegraph page: {e}")


def resize_image(image):
    im = Image.open(image)
    im.save(image, "PNG")


__mod_name__ = "Telegraph"
