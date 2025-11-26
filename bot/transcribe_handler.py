"""
Transcribe Handler for Telegram Bot
Optimized, stable and safe transcription system using Groq Whisper API.
"""

import os
import httpx
import aiofiles
from telegram import Update
from telegram.ext import ContextTypes

from config import config
from bot.handlers import check_subscription, get_subscription_keyboard

# Groq API settings
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"
TEMP_DIR = "temp_bot_audio"


# ---------------------- GROQ TRANSCRIPTION ----------------------

async def transcribe_audio_file(file_path: str) -> str:
    """Send audio to Groq Whisper API and return text."""
    if not config.GROQ_API_KEY:
        return "❌ GROQ_API_KEY sozlanmagan"

    try:
        mime_type = _detect_mime(file_path)

        async with aiofiles.open(file_path, "rb") as audio_file:
            file_content = await audio_file.read()

        files = {
            "file": (os.path.basename(file_path), file_content, mime_type),
        }
        data = {
            "model": WHISPER_MODEL,
            "response_format": "json",
            "temperature": 0.0
        }
        headers = {"Authorization": f"Bearer {config.GROQ_API_KEY}"}

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                GROQ_API_URL, files=files, data=data, headers=headers
            )

        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "").strip()
            return text if text else "❌ Matn topilmadi"

        return f"❌ API xatolik {response.status_code}"

    except Exception as e:
        return f"❌ Xatolik: {str(e)}"


def _detect_mime(file_path: str) -> str:
    """Auto-detect mime type."""
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        '.mp3': 'audio/mpeg',
        '.mp4': 'audio/mp4',
        '.m4a': 'audio/mp4',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.opus': 'audio/opus',
        '.flac': 'audio/flac',
        '.webm': 'audio/webm',
        '.mkv': 'video/mp4',
        '.mov': 'video/mp4',
        '.avi': 'video/mp4',
        '.wmv': 'video/mp4',
    }
    return mime_map.get(ext, 'audio/mpeg')


# ---------------------- COMMAND HANDLER ----------------------

async def transcribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /transcribe command."""
    is_subscribed, missing_channels = await check_subscription(
        context.bot, update.effective_user.id
    )

    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        await update.message.reply_text(
            f"❌ <b>Botdan foydalanish uchun kanallarga obuna bo'ling!</b>\n\n"
            f"<b>Obuna bo'lish kerak:</b>\n{channels_text}\n\n"
            f"Obuna bo'lgandan keyin yuboring.",
            reply_markup=get_subscription_keyboard(missing_channels),
            parse_mode="HTML"
        )
        return

    if not config.validate_groq():
        await update.message.reply_text(
            "❌ GROQ_API_KEY sozlanmagan.",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "🎙️ *Audio Transkript*\n\n"
        "Menga audio/xabar/video yuboring — matnga aylantiraman!",
        parse_mode="Markdown"
    )


# ---------------------- MEDIA HELPERS ----------------------

def _has_supported_media(message) -> bool:
    return (
        message.voice or message.audio or message.video or
        message.video_note or
        (message.document and message.document.mime_type and (
            message.document.mime_type.startswith("audio/") or
            message.document.mime_type.startswith("video/")
        ))
    )


async def _check_user_permissions(message, context) -> bool:
    is_subscribed, missing_channels = await check_subscription(
        context.bot, message.from_user.id
    )

    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        await message.reply_text(
            f"❌ <b>Botdan foydalanish uchun kanallarga obuna bo'ling!</b>\n\n"
            f"<b>Obuna bo'lish kerak:</b>\n{channels_text}",
            reply_markup=get_subscription_keyboard(missing_channels),
            parse_mode="HTML"
        )
        return False

    if not config.validate_groq():
        await message.reply_text("❌ GROQ_API_KEY sozlanmagan.")
        return False

    return True


async def _get_media_file(message):
    if message.voice: return await message.voice.get_file()
    if message.audio: return await message.audio.get_file()
    if message.video: return await message.video.get_file()
    if message.video_note: return await message.video_note.get_file()
    if message.document: return await message.document.get_file()
    return None


# ---------------------- RESULT SENDER ----------------------

async def _send_transcription_result(processing_msg, text, update):
    """Send transcription result safely without using edit_text()."""

    # Always try to delete processing message
    if processing_msg:
        try:
            await processing_msg.delete()
        except Exception:
            pass

    # Handle errors
    if text.startswith("❌"):
        await update.message.reply_text(text)
        return

    max_chunk = 3500
    footer = f"\n\n━━━━━━━━━━━━━━━━\n_{WHISPER_MODEL}_"

    # Short message
    if len(text) <= max_chunk:
        await update.message.reply_text(
            f"🎙️ *Transkript Natijasi*\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"{text}{footer}",
            parse_mode="Markdown"
        )
        return

    # Long message → split
    parts = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
    total = len(parts)

    # First part
    await update.message.reply_text(
        f"🎙️ *Transkript Natijasi* (1/{total})\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"{parts[0]}",
        parse_mode="Markdown"
    )

    # Remaining parts
    for idx in range(1, total):
        chunk = parts[idx]
        last = (idx == total - 1)

        await update.message.reply_text(
            f"*Qism {idx+1}/{total}*\n\n"
            f"{chunk}{footer if last else ''}",
            parse_mode="Markdown"
        )


# ---------------------- MAIN HANDLER ----------------------

async def handle_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not _has_supported_media(message):
        return

    if not await _check_user_permissions(message, context):
        return

    # FILE SIZE CHECK
    file_size = (
        message.voice.file_size if message.voice else
        message.audio.file_size if message.audio else
        message.video.file_size if message.video else
        message.document.file_size if message.document else
        0
    )

    if file_size > 25 * 1024 * 1024:
        await message.reply_text(
            "❌ *Fayl juda katta!* Maksimal 25 MB.",
            parse_mode="Markdown"
        )
        return

    processing_msg = await message.reply_text(
        f"🎙️ *Audio matnlashtirilmoqda...*\n"
        f"📊 Fayl hajmi: {file_size/1024/1024:.1f} MB\n"
        f"⏳ Iltimos kuting...",
        parse_mode="Markdown"
    )

    file_path = None

    try:
        os.makedirs(TEMP_DIR, exist_ok=True)

        file = await _get_media_file(message)
        file_path = os.path.join(TEMP_DIR, f"{message.message_id}.ogg")
        await file.download_to_drive(file_path)

        await processing_msg.edit_text(
            "🔄 *Whisper AI ishlayapti...*\n⏳ Kuting...",
            parse_mode="Markdown"
        )

        text = await transcribe_audio_file(file_path)

        await _send_transcription_result(processing_msg, text, update)

    except Exception as e:
        try:
            await processing_msg.edit_text(f"❌ Xatolik: {str(e)[:200]}")
        except:
            await message.reply_text(f"❌ Xatolik: {str(e)[:200]}")

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
