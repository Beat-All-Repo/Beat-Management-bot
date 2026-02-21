import re

import bs4
import requests
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from FallenRobot import dispatcher
from FallenRobot.modules.disable import DisableAbleCommandHandler


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_imdb(movie_name: str) -> dict:
    """Scrape IMDB and return a dict of movie details."""
    remove_space = movie_name.split(" ")
    final_name = "+".join(remove_space)

    search_url = f"https://www.imdb.com/find?ref_=nv_sr_fn&q={final_name}&s=all"
    page = requests.get(search_url, headers=HEADERS, timeout=10)
    soup = bs4.BeautifulSoup(page.content, "lxml")

    # Try new IMDB layout first, fall back to old
    odds = soup.findAll("tr", "odd") or soup.findAll("li", {"class": "find-result-item"})
    if not odds:
        return {}

    first = odds[0]
    link_tag = first.find("a")
    if not link_tag:
        return {}

    mov_title = link_tag.text.strip()
    mov_link = "https://www.imdb.com" + link_tag["href"].split("?")[0]

    page1 = requests.get(mov_link, headers=HEADERS, timeout=10)
    soup = bs4.BeautifulSoup(page1.content, "lxml")

    # Poster
    poster = ""
    if soup.find("div", "poster"):
        img = soup.find("div", "poster").find("img")
        if img:
            poster = img.get("src", "")

    # Details
    mov_details = ""
    if soup.find("div", "title_wrapper"):
        pg = soup.find("div", "title_wrapper").findNext("div").text
        mov_details = re.sub(r"\s+", " ", pg).strip()

    # Credits
    director = writer = stars = "Not available"
    credits = soup.findAll("div", "credit_summary_item")
    if len(credits) >= 1:
        director = credits[0].a.text if credits[0].a else "Not available"
    if len(credits) >= 3:
        writer = credits[1].a.text if credits[1].a else "Not available"
        actors = [x.text for x in credits[2].findAll("a")]
        if actors:
            actors = [a for a in actors if "full cast" not in a.lower()]
            stars = ", ".join(actors[:3])
    elif len(credits) == 2:
        writer = "Not available"
        actors = [x.text for x in credits[1].findAll("a")]
        if actors:
            actors = [a for a in actors if "full cast" not in a.lower()]
            stars = ", ".join(actors[:3])

    # Story line
    story_line = "Not available"
    if soup.find("div", "inline canwrap"):
        paras = soup.find("div", "inline canwrap").findAll("p")
        if paras:
            story_line = paras[0].text.strip()

    # Country / Language
    mov_country = mov_language = "Not available"
    info_blocks = soup.findAll("div", "txt-block")
    countries, languages = [], []
    for node in info_blocks:
        for a in node.findAll("a"):
            if "country_of_origin" in a.get("href", ""):
                countries.append(a.text)
            elif "primary_language" in a.get("href", ""):
                languages.append(a.text)
    if countries:
        mov_country = countries[0]
    if languages:
        mov_language = languages[0]

    # Rating
    mov_rating = "Not available"
    for r in soup.findAll("div", "ratingValue"):
        if r.strong:
            mov_rating = r.strong.get("title", "Not available")
            break

    return {
        "title": mov_title,
        "link": mov_link,
        "poster": poster,
        "details": mov_details,
        "rating": mov_rating,
        "country": mov_country,
        "language": mov_language,
        "director": director,
        "writer": writer,
        "stars": stars,
        "story": story_line,
    }


def imdb(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args

    if not args:
        message.reply_text(
            "Usage: `/imdb <movie or anime name>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    movie_name = " ".join(args)
    msg = message.reply_text(f"🔍 Searching IMDB for *{movie_name}*...", parse_mode=ParseMode.MARKDOWN)

    try:
        data = fetch_imdb(movie_name)
    except Exception as e:
        msg.edit_text(f"❌ Error fetching data: `{e}`", parse_mode=ParseMode.MARKDOWN)
        return

    if not data:
        msg.edit_text("❌ Movie not found! Please enter a valid name.")
        return

    caption = (
        f"<a href='{data['poster']}'>&#8203;</a>"
        f"<b>🎬 Title:</b> <code>{data['title']}</code>\n"
        f"<code>{data['details']}</code>\n"
        f"<b>⭐ Rating:</b> <code>{data['rating']}</code>\n"
        f"<b>🌍 Country:</b> <code>{data['country']}</code>\n"
        f"<b>🗣 Language:</b> <code>{data['language']}</code>\n"
        f"<b>🎥 Director:</b> <code>{data['director']}</code>\n"
        f"<b>✍️ Writer:</b> <code>{data['writer']}</code>\n"
        f"<b>🌟 Stars:</b> <code>{data['stars']}</code>\n\n"
        f"<b>📖 Story:</b> {data['story'][:500]}{'...' if len(data['story']) > 500 else ''}"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 View on IMDB", url=data["link"])]
    ])

    msg.delete()
    try:
        message.reply_text(
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=buttons,
            disable_web_page_preview=False,
        )
    except Exception:
        # If poster link causes issues, send without it
        message.reply_text(
            caption.replace(f"<a href='{data['poster']}'>&#8203;</a>", ""),
            parse_mode=ParseMode.HTML,
            reply_markup=buttons,
            disable_web_page_preview=True,
        )


IMDB_HANDLER = DisableAbleCommandHandler("imdb", imdb, run_async=True)
dispatcher.add_handler(IMDB_HANDLER)

__mod_name__ = "IMDb"
__command_list__ = ["imdb"]
__handlers__ = [IMDB_HANDLER]
__help__ = """
*IMDb Search:*
 • `/imdb <name>`*:* get IMDb details for any movie or anime.
"""
