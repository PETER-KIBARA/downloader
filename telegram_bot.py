import asyncio
import logging
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import yt_dlp

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://\S+")
ALLOWED_FORMATS = {"mp4", "mp3", "mov"}
ALLOWED_QUALITIES = {"720p": "720", "1080p": "1080", "4k": "2160"}


@dataclass
class UserPrefs:
    fmt: str = os.getenv("TELEGRAM_DEFAULT_FORMAT", "mp4")
    quality: str = os.getenv("TELEGRAM_DEFAULT_QUALITY", "1080p")


user_preferences: dict[int, UserPrefs] = {}


def get_allowed_users() -> set[int]:
    raw = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").strip()
    if not raw:
        return set()
    allowed = set()
    for item in raw.split(","):
        item = item.strip()
        if item.isdigit():
            allowed.add(int(item))
    return allowed


ALLOWED_USERS = get_allowed_users()
MAX_FILE_SIZE_BYTES = int(float(os.getenv("TELEGRAM_MAX_FILE_SIZE_MB", "1900")) * 1024 * 1024)
STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "/tmp/umd_downloads"))


def is_allowed(user_id: int) -> bool:
    if not ALLOWED_USERS:
        return True
    return user_id in ALLOWED_USERS


def get_prefs(user_id: int) -> UserPrefs:
    if user_id not in user_preferences:
        user_preferences[user_id] = UserPrefs()
    return user_preferences[user_id]


def extract_first_url(text: str) -> Optional[str]:
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None


def build_ydl_opts(output_file: Path, fmt: str, quality: str) -> dict:
    if fmt == "mp3":
        return {
            "quiet": True,
            "noplaylist": True,
            "format": "bestaudio/best",
            "outtmpl": str(output_file.with_suffix(".%(ext)s")),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

    max_height = ALLOWED_QUALITIES.get(quality, "1080")
    return {
        "quiet": True,
        "noplaylist": True,
        "format": f"bestvideo[height<={max_height}]+bestaudio/best/best[height<={max_height}]",
        "merge_output_format": fmt,
        "outtmpl": str(output_file.with_suffix(".%(ext)s")),
    }


def download_media(url: str, fmt: str, quality: str) -> Path:
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    base_name = f"media_{uuid.uuid4().hex}"
    output_hint = STORAGE_PATH / base_name

    ydl_opts = build_ydl_opts(output_hint, fmt, quality)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_path = Path(ydl.prepare_filename(info))

    if fmt == "mp3":
        mp3_path = downloaded_path.with_suffix(".mp3")
        if mp3_path.exists():
            return mp3_path

    if downloaded_path.exists():
        return downloaded_path

    candidates = sorted(STORAGE_PATH.glob(f"{base_name}*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError("Download finished but output file was not found")
    return candidates[0]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Access denied.")
        return

    prefs = get_prefs(user_id)
    await update.message.reply_text(
        "Send a media URL (YouTube, TikTok, Instagram, X, Facebook, Pinterest, LinkedIn).\n"
        f"Current format: {prefs.fmt} | quality: {prefs.quality}\n"
        "Commands:\n"
        "/format <mp4|mp3|mov>\n"
        "/quality <720p|1080p|4k>\n"
        "/help"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Usage:\n"
        "1) Optional: set format via /format mp4|mp3|mov\n"
        "2) Optional: set quality via /quality 720p|1080p|4k\n"
        "3) Send the link and wait for the file"
    )


async def set_format(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Access denied.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /format mp4|mp3|mov")
        return

    fmt = context.args[0].lower()
    if fmt not in ALLOWED_FORMATS:
        await update.message.reply_text("Invalid format. Use mp4, mp3, or mov.")
        return

    prefs = get_prefs(user_id)
    prefs.fmt = fmt
    await update.message.reply_text(f"Format set to {fmt}.")


async def set_quality(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Access denied.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /quality 720p|1080p|4k")
        return

    quality = context.args[0].lower()
    if quality not in ALLOWED_QUALITIES:
        await update.message.reply_text("Invalid quality. Use 720p, 1080p, or 4k.")
        return

    prefs = get_prefs(user_id)
    prefs.quality = quality
    await update.message.reply_text(f"Quality set to {quality}.")


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text("Access denied.")
        return

    text = update.message.text or ""
    url = extract_first_url(text)
    if not url:
        await update.message.reply_text("Please send a valid URL.")
        return

    prefs = get_prefs(user_id)
    status_msg = await update.message.reply_text(
        f"Processing... format={prefs.fmt}, quality={prefs.quality}"
    )

    output_file = None
    try:
        output_file = await asyncio.to_thread(download_media, url, prefs.fmt, prefs.quality)

        if output_file.stat().st_size > MAX_FILE_SIZE_BYTES:
            await status_msg.edit_text(
                "File is too large to send through this bot configuration. "
                f"Saved locally at: {output_file}"
            )
            return

        await status_msg.edit_text("Upload in progress...")

        if output_file.suffix.lower() == ".mp3":
            with output_file.open("rb") as f:
                await update.message.reply_audio(audio=f)
        elif output_file.suffix.lower() in {".mp4", ".mov"}:
            with output_file.open("rb") as f:
                await update.message.reply_video(video=f)
        else:
            with output_file.open("rb") as f:
                await update.message.reply_document(document=f)

        await status_msg.edit_text("Done ✅")

    except Exception as exc:
        logger.exception("Failed to process URL")
        await status_msg.edit_text(
            "Failed to download this link. It may be private, removed, unsupported, or temporarily unavailable."
        )
    finally:
        if output_file and output_file.exists():
            try:
                output_file.unlink()
            except OSError:
                logger.warning("Could not delete temp file: %s", output_file)


async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing. Set it in .env")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("format", set_format))
    app.add_handler(CommandHandler("quality", set_quality))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    logger.info("Telegram bot is starting...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
