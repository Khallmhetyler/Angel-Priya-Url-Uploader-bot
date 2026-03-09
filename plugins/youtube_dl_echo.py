#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import os
import shutil
import time
import urllib.parse

import filetype
import lk21
import pyrogram
import requests
import tldextract
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from helper_funcs.display_progress import humanbytes, progress_for_pyrogram
from helper_funcs.help_uploadbot import DownLoadFile
from translation import Translation

if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def _fmt_duration(seconds):
    if not seconds:
        return "Unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _extract_url_from_message(message: Message):
    text = message.text or ""
    if "|" in text:
        return text.split("|")[0].strip(), text
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_link":
                return entity.url, text
            if entity.type == "url":
                return text[entity.offset:entity.offset + entity.length], text
    return text.strip(), text


async def _handle_lk21(bot: Client, update: Message, url: str):
    file_name = None
    folder = f'./lk21/{update.from_user.id}/'
    pablo = await update.reply_text('LK21 link detected')
    await asyncio.sleep(1)
    if os.path.isdir(folder):
        await update.reply_text("Don't spam, wait till your previous task done.")
        await pablo.delete()
        return

    os.makedirs(folder)
    await pablo.edit_text('Downloading...')
    bypasser = lk21.Bypass()
    xurl = bypasser.bypass_url(url)
    if ' | ' in url:
        url_parts = url.split(' | ')
        file_name = url_parts[1]
    else:
        urlname = xurl.rsplit('/', 1)[-1]
        file_name = urllib.parse.unquote(urlname).replace('+', ' ')

    dldir = f'{folder}{file_name}'
    r = requests.get(xurl, allow_redirects=True)
    with open(dldir, 'wb') as fd:
        fd.write(r.content)

    try:
        guessed = filetype.guess(dldir)
        xfiletype = guessed.mime
    except Exception:
        xfiletype = file_name

    duration = 0
    if xfiletype in ['video/mp4', 'video/x-matroska', 'video/webm', 'audio/mpeg']:
        metadata = extractMetadata(createParser(dldir))
        if metadata is not None and metadata.has("duration"):
            duration = metadata.get('duration').seconds

    await pablo.edit_text('Uploading...')
    start_time = time.time()
    if xfiletype in ['video/mp4', 'video/x-matroska', 'video/webm']:
        await bot.send_video(
            chat_id=update.chat.id,
            video=dldir,
            caption=file_name,
            duration=duration,
            reply_to_message_id=update.id,
            progress=progress_for_pyrogram,
            progress_args=(Translation.UPLOAD_START, pablo, start_time)
        )
    elif xfiletype == 'audio/mpeg':
        await bot.send_audio(
            chat_id=update.chat.id,
            audio=dldir,
            caption=file_name,
            duration=duration,
            reply_to_message_id=update.id,
            progress=progress_for_pyrogram,
            progress_args=(Translation.UPLOAD_START, pablo, start_time)
        )
    else:
        await bot.send_document(
            chat_id=update.chat.id,
            document=dldir,
            caption=file_name,
            reply_to_message_id=update.id,
            progress=progress_for_pyrogram,
            progress_args=(Translation.UPLOAD_START, pablo, start_time)
        )
    await pablo.delete()
    shutil.rmtree(folder)


@pyrogram.Client.on_message(pyrogram.filters.regex(pattern=".*http.*"))
async def echo(bot: Client, update: Message):
    if update.from_user.id not in Config.AUTH_USERS:
        return

    url, raw_text = _extract_url_from_message(update)
    youtube_dl_username = None
    youtube_dl_password = None

    if "|" in raw_text:
        parts = [x.strip() for x in raw_text.split("|")]
        if len(parts) == 4:
            youtube_dl_username = parts[2]
            youtube_dl_password = parts[3]

    ext = tldextract.extract(url)
    if ext.domain in ['zippyshare', 'hxfile', 'mediafire', 'anonfiles', 'antfiles']:
        await _handle_lk21(bot, update, raw_text)
        return

    command_to_exec = ["yt-dlp", "--no-warnings", "--youtube-skip-dash-manifest", "-j", url]
    if Config.HTTP_PROXY:
        command_to_exec.extend(["--proxy", Config.HTTP_PROXY])
    if youtube_dl_username:
        command_to_exec.extend(["--username", youtube_dl_username])
    if youtube_dl_password:
        command_to_exec.extend(["--password", youtube_dl_password])

    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    if e_response and "nonnumeric port" not in e_response:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format(str(e_response)),
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    if not t_response:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format("Unsupported or empty response"),
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    x_response = t_response.split("\n")[0]
    response_json = json.loads(x_response)
    save_ytdl_json_path = f"{Config.DOWNLOAD_LOCATION}/{update.from_user.id}.json"
    with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
        json.dump(response_json, outfile, ensure_ascii=False)

    duration = response_json.get("duration")
    title = response_json.get("title", "Unknown title")

    quality_rows = []
    seen = set()
    for fmt in response_json.get("formats", []):
        fmt_id = fmt.get("format_id")
        fmt_ext = fmt.get("ext")
        vcodec = fmt.get("vcodec")
        height = fmt.get("height")
        if not fmt_id or not fmt_ext or vcodec in (None, "none") or not height:
            continue
        key = (height, fmt_ext)
        if key in seen:
            continue
        seen.add(key)
        size_text = humanbytes(fmt.get("filesize") or fmt.get("filesize_approx") or 0) or "~"
        quality_rows.append((height, InlineKeyboardButton(
            text=f"{height}p • {size_text}",
            callback_data=f"video|{fmt_id}|{fmt_ext}".encode("UTF-8")
        )))

    quality_rows = sorted(quality_rows, key=lambda x: x[0])
    inline_keyboard = [[btn] for _, btn in quality_rows[:12]]

    if duration is not None:
        inline_keyboard.append([
            InlineKeyboardButton("MP3 128 kbps", callback_data="audio|128k|mp3".encode("UTF-8")),
            InlineKeyboardButton("MP3 320 kbps", callback_data="audio|320k|mp3".encode("UTF-8")),
        ])

    if not inline_keyboard:
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format("No downloadable video formats found"),
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    thumbnail_image = response_json.get("thumbnail") or Config.DEF_THUMB_NAIL_VID_S
    thumb_image_path = DownLoadFile(
        thumbnail_image,
        f"{Config.DOWNLOAD_LOCATION}/{update.from_user.id}.webp",
        Config.CHUNK_SIZE,
        None,
        Translation.DOWNLOAD_START,
        update.id,
        update.chat.id,
    )
    caption = (
        f"Title: {title}\n"
        f"Duration: {_fmt_duration(duration)}\n"
        f"Choose your download quality:"
    )

    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    if thumb_image_path and os.path.exists(thumb_image_path):
        jpg_thumb = thumb_image_path.replace(".webp", ".jpg")
        Image.open(thumb_image_path).convert("RGB").save(jpg_thumb, "jpeg")
        await bot.send_photo(
            chat_id=update.chat.id,
            photo=jpg_thumb,
            caption=caption,
            reply_markup=reply_markup,
            reply_to_message_id=update.id,
        )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=caption,
            reply_markup=reply_markup,
            reply_to_message_id=update.id,
        )
