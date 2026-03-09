<img src="https://telegra.ph/file/efdf5689646da738eb787.jpg" alt="logo" target="/blank">

<h1 align="center">
 <b><a href="https://telegram.me/LazyDeveloper" target="/blank">BEWAFA Angel-Priya BOT</a></>
</h1>

<p align="center">🤍 Thanks for Being Here 🤍</p>


## * MiND iT....
👉 Only Auth Users (AUTH_USERS) Can Use The Bot

👉 Upload [YTDL Supported Links](https://ytdl-org.github.io/youtube-dl/supportedsites.html) to Telegram.

👉 Upload HTTP/HTTPS as File/Video to Telegram.

👉 Upload Mediafire, Zippyshare, Hxfile, Anonfiles, Antfiles URL using LK21

### ⚡️ Configs 

* `TG_BOT_TOKEN`  - Create a New BOT to Get bot token. follow link  https://telegram.me/BotFather

* `API_ID` (or `APP_ID`) - From my.telegram.org 

* `API_HASH` - From my.telegram.org 

* `AUTH_USERS`  - Your Telegram + Your paid users id.
  - NOTE - Only `AUTH_USERS` can use this BOT. SO you must have to give your id.

* `LAZY_DEVELOPER` - Give ADMIN id in this field. (`LAZY_ADMIN` also supported)

* `DEF_THUMB_NAIL_VID_S` - default thumbnail to be used in the videos. Incase, yt-dlp is unable to find a thumbnail.

* `LOG_CHANNEL` - Optional channel/group id where uploads are forwarded for logging.

* `HTTP_PROXY` - Optional proxy for georestricted sites.

## 🚀 Deploy (Telegram bot)

### 1) Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TG_BOT_TOKEN="123456:ABC..."
export API_ID="123456"
export API_HASH="your_api_hash"
export AUTH_USERS="123456789"
export LAZY_DEVELOPER="123456789"
python3 bot.py
```

### 2) Docker run

```bash
docker build -t angel-priya-bot .
docker run --rm \
  -e TG_BOT_TOKEN="123456:ABC..." \
  -e API_ID="123456" \
  -e API_HASH="your_api_hash" \
  -e AUTH_USERS="123456789" \
  -e LAZY_DEVELOPER="123456789" \
  angel-priya-bot
```

### 3) Heroku/Koyeb
Use worker process (`python3 bot.py`) and set the same environment variables in dashboard/secrets.

> Note: Downloading content from YouTube may be restricted by YouTube Terms of Service and local laws. Use responsibly.

### 🔗 important_Links
- [❣️ Join Youtube](https://www.youtube.com/channel/UCY-iDra0x2hdd9PdHKcZkRw)


#### 🧡 Respecting Lazy... 🧡
- [🔥 LazyDeveloperr](https://github.com/LazyDeveloperr) 
- [🔥 Instagram](https://www.instagram.com/LazyDeveloperrr) 
- [🔥 Pyrogram](https://github.com/pyrogram/pyrogram)


**Features**:
👉 Upload [yt-dlp Supported Links](https://ytdl-org.github.io/youtube-dl/supportedsites.html) to Telegram.

🧡 Upload HTTP/HTTPS as File/Video to Telegram.

🧡 Upload zee5, sony.live, voot and much more.

🧡 Permanent thumbnail Support.

🧡 Broadcast message.

## Credits, and Thanks to
* [@LazyDeveloper](https://telegram.me/mRiderDM) LazyDeveloper
* [@SpEcHlDe](https://t.me/ThankTelegram) for his [AnyDLBot](https://telegram.dog/AnyDLBot)
* [Dan Tès](https://t.me/haskell) for his [Pyrogram Library](https://github.com/pyrogram/pyrogram)
* [Yoily](https://t.me/YoilyL) for his [UploaditBot](https://telegram.dog/UploaditBot)

#### LICENSE
- GPLv3
