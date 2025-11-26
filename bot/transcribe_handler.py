"""
Transcribe Handler for Telegram Bot
Allows users to transcribe audio/voice messages using the bot.
"""

import os
import httpx
import aiofiles
from telegram import Update
from telegram.ext import ContextTypes

from config import config
from bot.handlers import check_subscription, get_subscription_keyboard

# Audio format constants
AUDIO_MPEG = 'audio/mpeg'
AUDIO_MP4 = 'audio/mp4'
AUDIO_WAV = 'audio/wav'
AUDIO_OGG = 'audio/ogg'
AUDIO_OPUS = 'audio/opus'
AUDIO_FLAC = 'audio/flac'
AUDIO_WEBM = 'audio/webm'

# Supported audio formats for Groq Whisper API
SUPPORTED_AUDIO_FORMATS = {
    AUDIO_MPEG: '.mp3',
    AUDIO_MP4: '.m4a',
    AUDIO_WAV: '.wav',
    AUDIO_OGG: '.ogg',
    AUDIO_OPUS: '.opus',
    AUDIO_FLAC: '.flac',
    AUDIO_WEBM: '.webm',
}

# Groq API settings
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"
TEMP_DIR = "temp_bot_audio"


async def transcribe_audio_file(file_path: str) -> str:
    """Transcribe audio using Groq Whisper API."""
    if not config.GROQ_API_KEY:
        return "❌ GROQ_API_KEY sozlanmagan"
    
    try:
        # Auto-detect MIME type from file extension
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.mp3': AUDIO_MPEG,
            '.mp4': AUDIO_MP4,
            '.m4a': AUDIO_MP4,
            '.wav': AUDIO_WAV,
            '.ogg': AUDIO_OGG,
            '.oga': AUDIO_OGG,
            '.opus': AUDIO_OPUS,
            '.flac': AUDIO_FLAC,
            '.webm': AUDIO_WEBM,
            '.mpga': AUDIO_MPEG,
            '.mpeg': AUDIO_MPEG,
            # Video files
            '.mkv': AUDIO_MP4,
            '.avi': AUDIO_MP4,
            '.mov': AUDIO_MP4,
            '.wmv': AUDIO_MP4,
        }
        mime_type = mime_types.get(ext, AUDIO_MPEG)
        
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
            headers = {
                "Authorization": f"Bearer {config.GROQ_API_KEY}"
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    GROQ_API_URL,
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    text = result.get("text", "").strip()
                    if not text:
                        return "❌ Matn topilmadi"
                    return text
                else:
                    return f"❌ API xatolik {response.status_code}"
    
    except Exception as e:
        return f"❌ Xatolik: {str(e)}"


async def transcribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /transcribe command."""
    # Check subscription
    is_subscribed, missing_channels = await check_subscription(context.bot, update.effective_user.id)
    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        await update.message.reply_text(
            f"❌ <b>Botdan foydalanish uchun kanallarga obuna bo'ling!</b>\n\n"
            f"<b>Obuna bo'lish kerak:</b>\n{channels_text}\n\n"
            f"Obuna bo'lgandan keyin ✅ Obunani tekshirish tugmasini bosing.",
            reply_markup=get_subscription_keyboard(missing_channels),
            parse_mode="HTML"
        )
        return
    
    # Check if Groq API is configured
    if not config.validate_groq():
        await update.message.reply_text(
            "❌ **Audio transkript funksiyasi ishlamayapti**\n\n"
            "GROQ_API_KEY sozlanmagan.",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text(
        "🎙️ **Audio Transkript**\n\n"
        "Menga audio fayl, ovozli xabar yoki video yuboring - matnga aylantiraman!\n\n"
        "**Qo'llab-quvvatlanadigan formatlar:**\n"
        "• Ovozli xabarlar 🎤\n"
        "• Audio fayllar 🎵 (MP3, WAV, OGG va boshqalar)\n"
        "• Videolar 🎬\n\n"
        "**Tillar:** Avtomatik aniqlash (90+ til)\n"
        "**Model:** Whisper AI (whisper-large-v3-turbo)",
        parse_mode="Markdown"
    )


def _has_supported_media(message) -> bool:
    """Check if message contains supported media for transcription."""
    return (
        message.audio or 
        message.voice or 
        message.video or 
        message.video_note or
        (message.document and message.document.mime_type and 
         (message.document.mime_type.startswith("audio/") or 
          message.document.mime_type.startswith("video/")))
    )


async def _check_user_permissions(message, context) -> bool:
    """Check subscription and API configuration. Returns True if allowed."""
    # Check subscription
    is_subscribed, missing_channels = await check_subscription(context.bot, message.from_user.id)
    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        await message.reply_text(
            f"❌ <b>Botdan foydalanish uchun kanallarga obuna bo'ling!</b>\n\n"
            f"<b>Obuna bo'lish kerak:</b>\n{channels_text}\n\n"
            f"Obuna bo'lgandan keyin audio/video yuboring.",
            reply_markup=get_subscription_keyboard(missing_channels),
            parse_mode="HTML"
        )
        return False
    
    # Check if Groq API is configured
    if not config.validate_groq():
        return False
    
    return True


async def _get_media_file(message):
    """Get file object from message based on media type."""
    if message.voice:
        return await message.voice.get_file()
    elif message.audio:
        return await message.audio.get_file()
    elif message.video:
        return await message.video.get_file()
    elif message.video_note:
        return await message.video_note.get_file()
    elif message.document:
        return await message.document.get_file()
    return None


async def _send_transcription_result(processing_msg, text, update):
    """Send transcription result - always delete processing msg and send new."""
    # Always delete processing message first
    try:
        await processing_msg.delete()
    except Exception:
        pass
    
    # Handle errors
    if text.startswith("❌"):
        await update.message.reply_text(text)
        return
    
    # Safe chunk size (Telegram limit is 4096, we use 3500 for safety)
    max_chunk = 3500
    footer = f"\n\n━━━━━━━━━━━━━━━━\n_{WHISPER_MODEL}_"
    
    if len(text) <= max_chunk:
        # Single message
        await update.message.reply_text(
            f"🎙️ **Transkript Natijasi**\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"{text}{footer}",
            parse_mode="Markdown"
        )
    else:
        # Split into multiple messages
        total_parts = (len(text) // max_chunk) + 1
        
        # Send first part
        await update.message.reply_text(
            f"🎙️ **Transkript Natijasi** (1/{total_parts})\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"{text[:max_chunk]}",
            parse_mode="Markdown"
        )
        
        # Send remaining parts
        remaining = text[max_chunk:]
        part = 2
        while remaining:
            chunk = remaining[:max_chunk]
            remaining = remaining[max_chunk:]
            
            if remaining:
                await update.message.reply_text(
                    f"**Qism {part}/{total_parts}**\n\n{chunk}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"**Qism {part}/{total_parts}**\n\n{chunk}{footer}",
                    parse_mode="Markdown"
                )
            part += 1


async def handle_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio/voice/video messages for transcription."""
    message = update.message
    
    # Quick checks
    if not _has_supported_media(message):
        return
    
    if not await _check_user_permissions(message, context):
        return
    
    # Check file size first
    file_size = 0
    if message.voice:
        file_size = message.voice.file_size or 0
    elif message.audio:
        file_size = message.audio.file_size or 0
        duration = message.audio.duration or 0
        if duration > 600:  # 10 minutes
            await message.reply_text(
                "❌ **Audio juda uzun!**\n\n"
                f"**Davomiyligi:** {duration//60} daqiqa {duration%60} sekund\n"
                "**Maksimal:** 10 daqiqa\n\n"
                "Qisqaroq audio yuboring.",
                parse_mode="Markdown"
            )
            return
    elif message.video:
        file_size = message.video.file_size or 0
        duration = message.video.duration or 0
        if duration > 600:  # 10 minutes
            await message.reply_text(
                "❌ **Video juda uzun!**\n\n"
                f"**Davomiyligi:** {duration//60} daqiqa {duration%60} sekund\n"
                "**Maksimal:** 10 daqiqa\n\n"
                "Qisqaroq video yuboring.",
                parse_mode="Markdown"
            )
            return
    elif message.document:
        file_size = message.document.file_size or 0
    
    # Check file size (25MB limit for Groq)
    if file_size > 25 * 1024 * 1024:  # 25MB
        await message.reply_text(
            "❌ **Fayl juda katta!**\n\n"
            f"**Hajmi:** {file_size/(1024*1024):.1f} MB\n"
            "**Maksimal:** 25 MB\n\n"
            "Kichikroq fayl yuboring.",
            parse_mode="Markdown"
        )
        return
    
    # Send processing message with estimated time
    estimated_time = "bir necha sekund"
    if file_size > 5 * 1024 * 1024:  # 5MB+
        estimated_time = "1-2 daqiqa"
    elif file_size > 1024 * 1024:  # 1MB+
        estimated_time = "30-60 sekund"
    
    processing_msg = await message.reply_text(
        f"🎙️ **Audio matnlashtirilmoqda...**\n\n"
        f"📊 **Fayl hajmi:** {file_size/(1024*1024):.1f} MB\n"
        f"⏱️ **Taxminiy vaqt:** {estimated_time}\n\n"
        f"⏳ Iltimos, kuting...",
        parse_mode="Markdown"
    )
    
    try:
        # Create temp directory
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Get media file
        file = await _get_media_file(message)
        if not file:
            await processing_msg.edit_text("❌ Qo'llab-quvvatlanmaydigan media turi")
            return
        
        # Download to temp file
        file_path = os.path.join(TEMP_DIR, f"audio_{update.message.message_id}.ogg")
        await file.download_to_drive(file_path)
        
        # Update status with file info
        file_info = f"📁 {os.path.basename(file_path)} ({file_size/(1024*1024):.1f} MB)"
        await processing_msg.edit_text(
            f"🔄 **Whisper AI bilan ishlanmoqda...**\n\n"
            f"{file_info}\n"
            f"🤖 **Model:** {WHISPER_MODEL}\n\n"
            f"⏳ Kuting, bu biroz vaqt olishi mumkin...",
            parse_mode="Markdown"
        )
        
        # Transcribe
        text = await transcribe_audio_file(file_path)
        
        # Cleanup
        try:
            os.remove(file_path)
        except OSError:
            pass  # Ignore file delete errors
        
        # Send result
        await _send_transcription_result(processing_msg, text, update)
    
    except Exception as e:
        error_msg = f"❌ Xatolik: {str(e)[:200]}"  # Truncate long errors
        try:
            await processing_msg.edit_text(error_msg)
        except Exception:
            try:
                await processing_msg.delete()
            except Exception:
                pass
            await update.message.reply_text(error_msg)
        # Cleanup on error
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass  # Ignore file delete errors
