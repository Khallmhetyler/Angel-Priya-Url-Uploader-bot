import os


def _get_env(name, default=""):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip()


def _get_int_env(name, default):
    raw_value = _get_env(name, "")
    if raw_value == "":
        return default
    return int(raw_value)


class Config(object):
    # get a token from @BotFather
    TG_BOT_TOKEN = _get_env("TG_BOT_TOKEN", "")
    # The Telegram API things
    APP_ID = _get_int_env("APP_ID", _get_int_env("API_ID", 12345))
    API_HASH = _get_env("API_HASH", "")
    # Get these values from my.telegram.org
    # Array to store users who are authorized to use the bot
    AUTH_USERS = set(int(x) for x in _get_env("AUTH_USERS", "").split())
    # the download location, where the HTTP Server runs
    DOWNLOAD_LOCATION = "./DOWNLOADS"
    # Telegram maximum file upload size
    MAX_FILE_SIZE = 50000000
    TG_MAX_FILE_SIZE = 2097152000
    FREE_USER_MAX_FILE_SIZE = 50000000
    # chunk size that should be used with requests
    CHUNK_SIZE = _get_int_env("CHUNK_SIZE", 128)
    # default thumbnail to be used in the videos
    DEF_THUMB_NAIL_VID_S = _get_env("DEF_THUMB_NAIL_VID_S", "https://telegra.ph/file/1efd13f55ef33d64aa2c8.jpg")
    # proxy for accessing youtube-dl in GeoRestricted Areas
    # Get your own proxy from https://github.com/rg3/youtube-dl/issues/1091#issuecomment-230163061
    HTTP_PROXY = _get_env("HTTP_PROXY", "")
    # LOGGER INFO CHANNEL ID
    LOG_CHANNEL = _get_int_env("LOG_CHANNEL", -100)
    # Give Admin id in this field
    LAZY_DEVELOPER = set(
        int(x) for x in (_get_env("LAZY_ADMIN") or _get_env("LAZY_DEVELOPER", "")).split()
    )
    # maximum message length in Telegram
    MAX_MESSAGE_LENGTH = 40960
    # set timeout for subprocess
    PROCESS_MAX_TIMEOUT = 3600
    # watermark file
    DEF_WATER_MARK_FILE = ""
