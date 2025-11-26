"""
Audio Transcription Module - Universal Speech to Text
Transcribes ANY audio format to text using Whisper AI.
Auto-detects language. Works with voice messages, audio files, videos.
Usage: Reply to any audio/voice/video with .transcribe
"""

import os
import sys
import httpx
import aiofiles
from typing import Optional

from telethon import TelegramClient, events

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config
from userbot.loader import ModuleInfo

# Global vars
_client: Optional[TelegramClient] = None
_owner_id: Optional[int] = None

# API config
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-large-v3-turbo"
TEMP_DIR = "temp_audio"

# Audio format constants
AUDIO_MPEG = 'audio/mpeg'
AUDIO_MP4 = 'audio/mp4'
AUDIO_WAV = 'audio/wav'
AUDIO_OGG = 'audio/ogg'
AUDIO_OPUS = 'audio/opus'
AUDIO_FLAC = 'audio/flac'
AUDIO_WEBM = 'audio/webm'


async def transcribe_audio(file_path: str) -> str:
    """Transcribe any audio to text. Auto-detects language."""
    if not config.GROQ_API_KEY:
        return "❌ GROQ_API_KEY sozlanmagan"
    
    try:
        # Get file extension and determine MIME type
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
            # Video files (audio will be extracted)
            '.mkv': AUDIO_MP4,
            '.avi': AUDIO_MP4,
            '.mov': AUDIO_MP4,
            '.wmv': AUDIO_MP4,
        }
        # Default to mp3 if unknown
        mime_type = mime_types.get(ext, AUDIO_MPEG)
        
        async with aiofiles.open(file_path, "rb") as audio_file:
            file_content = await audio_file.read()
            files = {
                "file": (os.path.basename(file_path), file_content, mime_type),
            }
            data = {
                "model": WHISPER_MODEL,
                # No language specified = auto-detect
                "response_format": "json",
                "temperature": 0.0  # More accurate
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
                    return f"❌ API xatolik {response.status_code}: {response.text[:200]}"
    
    except Exception as e:
        return f"❌ Xatolik: {str(e)}"


async def _safe_edit(msg, event, text: str):
    """Safely edit message, fallback to respond if edit fails."""
    try:
        await msg.edit(text)
    except Exception:
        try:
            await msg.delete()
        except Exception:
            pass
        await event.respond(text)


async def _send_result(event, text: str):
    """Send transcription result, splitting if too long."""
    max_chunk = 3500
    footer = f"\n\n━━━━━━━━━━━━━━━━\n_{WHISPER_MODEL}_"
    
    if len(text) <= max_chunk:
        await event.respond(
            f"🎙️ **Transkript**\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"{text}{footer}"
        )
        return
    
    # Split long text
    parts = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
    total = len(parts)
    
    # First part
    await event.respond(
        f"🎙️ **Transkript** (1/{total})\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"{parts[0]}"
    )
    
    # Remaining parts
    for idx in range(1, total):
        last = (idx == total - 1)
        await event.respond(
            f"**Qism {idx+1}/{total}**\n\n"
            f"{parts[idx]}{footer if last else ''}"
        )


async def handle_transcribe(event):
    """Universal transcription handler - works with any media."""
    reply_msg = await event.get_reply_message()
    
    if not reply_msg:
        await event.respond(
            "💡 **Foydalanish:** Audio/voice/video xabarga javob berib `.transcribe` yozing"
        )
        return
    
    # Check for any media
    if not reply_msg.media:
        await event.respond("❌ Xabarda media topilmadi!")
        return
    
    # Check file size (25MB limit for Groq)
    file_size = 0
    if hasattr(reply_msg, 'file') and reply_msg.file:
        file_size = reply_msg.file.size or 0
    
    if file_size > 25 * 1024 * 1024:
        await event.respond(
            f"❌ **Fayl juda katta!**\n\n"
            f"**Hajmi:** {file_size/(1024*1024):.1f} MB\n"
            f"**Maksimal:** 25 MB"
        )
        return
    
    processing_msg = await event.respond(
        f"🎙️ Yuklanmoqda... ({file_size/(1024*1024):.1f} MB)"
    )
    
    file_path = None
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Download media
        file_path = await reply_msg.download_media(file=TEMP_DIR)
        
        if not file_path:
            await _safe_edit(processing_msg, event, "❌ Media yuklanmadi")
            return
        
        # Check if file exists
        if not os.path.exists(file_path):
            await _safe_edit(processing_msg, event, "❌ Yuklangan fayl topilmadi")
            return
        
        # Transcribe
        await _safe_edit(processing_msg, event, "🔄 Whisper AI bilan matnga aylantirilmoqda...")
        text = await transcribe_audio(file_path)
        
        # Cleanup
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        # Result - delete processing msg and send new
        try:
            await processing_msg.delete()
        except Exception:
            pass
        
        if text.startswith("❌"):
            await event.respond(text)
        else:
            await _send_result(event, text)
    
    except Exception as e:
        error_msg = f"❌ Xatolik: {str(e)[:200]}"
        await _safe_edit(processing_msg, event, error_msg)
        # Cleanup on error
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


def setup(client: TelegramClient, loader) -> ModuleInfo:
    """Setup transcription module."""
    global _client, _owner_id
    _client = client
    _owner_id = loader.owner_id
    
    if not config.validate_groq():
        print("   ⚠️ Transcription: GROQ_API_KEY not configured")
        return ModuleInfo(
            name="Audio Transcription",
            description="Universal audio/voice/video to text (DISABLED - no API key)",
            commands=[]
        )
    
    module_info = ModuleInfo(
        name="Audio Transcription",
        description="Universal audio/voice/video to text (Whisper AI, any language)",
        commands=["transcribe"]
    )
    
    # Single universal command
    @client.on(events.NewMessage(pattern=r"^\.transcribe$", outgoing=True))
    async def transcribe_cmd(event):
        """Universal transcription command."""
        if _owner_id and event.sender_id != _owner_id:
            return
        
        try:
            await event.delete()
        except Exception:
            pass  # Ignore delete errors
        
        await handle_transcribe(event)
    
    return module_info
