#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import glob
import hashlib
import json
import logging
import os
import shutil
import time
from datetime import datetime

import pyrogram
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper_funcs.display_progress import humanbytes, progress_for_pyrogram
from helper_funcs.help_Nekmo_ffmpeg import generate_screen_shots
from pyrogram.types import InputMediaPhoto
from translation import Translation

if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def _cache_key(url, fmt, ext, send_type):
    raw = f"{url}|{fmt}|{ext}|{send_type}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _parse_source_url(reply_text, entities):
    youtube_dl_url = reply_text or ""
    custom_file_name = None
    username = None
    password = None

    if "|" in youtube_dl_url:
        url_parts = [x.strip() for x in youtube_dl_url.split("|")]
        if len(url_parts) >= 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        if len(url_parts) == 4:
            username = url_parts[2]
            password = url_parts[3]
    elif entities:
        for entity in entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                youtube_dl_url = youtube_dl_url[entity.offset:entity.offset + entity.length]
    return youtube_dl_url.strip(), custom_file_name, username, password


async def youtube_dl_call_back(bot, update):
    tg_send_type, youtube_dl_format, youtube_dl_ext = update.data.split("|")
    thumb_image_path = f"{Config.DOWNLOAD_LOCATION}/{update.from_user.id}.jpg"
    save_ytdl_json_path = f"{Config.DOWNLOAD_LOCATION}/{update.from_user.id}.json"

    try:
        with open(save_ytdl_json_path, "r", encoding="utf8") as f:
            response_json = json.load(f)
    except FileNotFoundError:
        await bot.answer_callback_query(update.id, "Session expired. Please send the URL again.", show_alert=True)
        return

    if not update.message.reply_to_message:
        await bot.answer_callback_query(update.id, "Missing source URL message.", show_alert=True)
        return

    youtube_dl_url, custom_name, youtube_dl_username, youtube_dl_password = _parse_source_url(
        update.message.reply_to_message.text,
        update.message.reply_to_message.entities,
    )

    default_name = f"{response_json.get('title', 'video')}_{youtube_dl_format}.{youtube_dl_ext}"
    custom_file_name = (custom_name or default_name).strip()

    await bot.edit_message_caption(
        chat_id=update.message.chat.id,
        message_id=update.message.message_id,
        caption=f"{Translation.DOWNLOAD_START}\nFormat: {youtube_dl_format}",
    )

    tmp_directory_for_each_user = f"{Config.DOWNLOAD_LOCATION}/{update.from_user.id}"
    os.makedirs(tmp_directory_for_each_user, exist_ok=True)

    cache_dir = f"{Config.DOWNLOAD_LOCATION}/cache"
    os.makedirs(cache_dir, exist_ok=True)
    cache_key = _cache_key(youtube_dl_url, youtube_dl_format, youtube_dl_ext, tg_send_type)
    cache_matches = glob.glob(f"{cache_dir}/{cache_key}.*")

    download_directory = f"{tmp_directory_for_each_user}/{custom_file_name}"
    cache_hit = bool(cache_matches)

    start = datetime.now()
    if cache_hit:
        shutil.copy2(cache_matches[0], download_directory)
    else:
        if tg_send_type == "audio":
            command_to_exec = [
                "yt-dlp", "-c", "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
                "--prefer-ffmpeg", "--extract-audio", "--audio-format", youtube_dl_ext,
                "--audio-quality", youtube_dl_format, youtube_dl_url, "-o", download_directory,
            ]
        else:
            minus_f_format = youtube_dl_format + "+bestaudio" if "youtu" in youtube_dl_url else youtube_dl_format
            command_to_exec = [
                "yt-dlp", "-c", "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
                "--embed-subs", "-f", minus_f_format, "--hls-prefer-ffmpeg", youtube_dl_url,
                "-o", download_directory,
            ]
        if Config.HTTP_PROXY:
            command_to_exec.extend(["--proxy", Config.HTTP_PROXY])
        if youtube_dl_username:
            command_to_exec.extend(["--username", youtube_dl_username])
        if youtube_dl_password:
            command_to_exec.extend(["--password", youtube_dl_password])
        command_to_exec.append("--no-warnings")

        process = await asyncio.create_subprocess_exec(
            *command_to_exec,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        if e_response and process.returncode != 0:
            await bot.edit_message_caption(
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                caption=Translation.NO_VOID_FORMAT_FOUND.format(e_response[:900]),
            )
            return

    if not os.path.exists(download_directory):
        alt = os.path.splitext(download_directory)[0] + ".mkv"
        if os.path.exists(alt):
            download_directory = alt
        else:
            await bot.edit_message_caption(
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                caption=Translation.NO_VOID_FORMAT_FOUND.format("Download failed."),
            )
            return

    if not cache_hit:
        _, ext = os.path.splitext(download_directory)
        shutil.copy2(download_directory, f"{cache_dir}/{cache_key}{ext}")

    end_one = datetime.now()
    file_size = os.stat(download_directory).st_size
    if file_size > Config.TG_MAX_FILE_SIZE:
        await bot.edit_message_caption(
            chat_id=update.message.chat.id,
            message_id=update.message.message_id,
            caption=Translation.RCHD_TG_API_LIMIT.format((end_one - start).seconds, humanbytes(file_size)),
        )
        return

    await bot.edit_message_caption(
        chat_id=update.message.chat.id,
        message_id=update.message.message_id,
        caption=f"{Translation.UPLOAD_START}\n{'(served from cache)' if cache_hit else ''}",
    )

    width = height = duration = 0
    if tg_send_type != "file":
        metadata = extractMetadata(createParser(download_directory))
        if metadata is not None and metadata.has("duration"):
            duration = metadata.get('duration').seconds

    if os.path.exists(thumb_image_path):
        Image.open(thumb_image_path).convert("RGB").save(thumb_image_path)
        metadata = extractMetadata(createParser(thumb_image_path))
        if metadata and metadata.has("width"):
            width = metadata.get("width")
        if metadata and metadata.has("height"):
            height = metadata.get("height")
    else:
        thumb_image_path = None

    description = response_json.get("fulltitle", "Uploaded by bot")[:1021]
    start_time = time.time()
    if tg_send_type == "audio":
        await bot.send_audio(
            chat_id=update.message.chat.id,
            audio=download_directory,
            caption=description,
            parse_mode="HTML",
            duration=duration,
            thumb=thumb_image_path,
            reply_to_message_id=update.message.reply_to_message.message_id,
            progress=progress_for_pyrogram,
            progress_args=(Translation.UPLOAD_START, update.message, start_time),
        )
    else:
        await bot.send_video(
            chat_id=update.message.chat.id,
            video=download_directory,
            caption=description,
            parse_mode="HTML",
            duration=duration,
            width=width,
            height=height,
            supports_streaming=True,
            thumb=thumb_image_path,
            reply_to_message_id=update.message.reply_to_message.message_id,
            progress=progress_for_pyrogram,
            progress_args=(Translation.UPLOAD_START, update.message, start_time),
        )

    images = await generate_screen_shots(download_directory, tmp_directory_for_each_user, False, Config.DEF_WATER_MARK_FILE, 300, 9)
    media_album_p = []
    if images:
        for i, image in enumerate(images):
            if os.path.exists(str(image)):
                media_album_p.append(InputMediaPhoto(media=image, caption="© @LazyDeveloperr" if i == 0 else None, parse_mode="html" if i == 0 else None))
    if media_album_p:
        await bot.send_media_group(chat_id=update.message.chat.id, disable_notification=True, reply_to_message_id=update.message.message_id, media=media_album_p)

    end_two = datetime.now()
    try:
        shutil.rmtree(tmp_directory_for_each_user)
    except Exception:
        pass

    await bot.edit_message_caption(
        chat_id=update.message.chat.id,
        message_id=update.message.message_id,
        caption=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format((end_one - start).seconds, (end_two - end_one).seconds),
    )
