"""
Audio to Voice Message Handler
Converts audio files to voice messages using FFmpeg
"""

import os
import tempfile
import asyncio
import logging
from pathlib import Path
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode

from config import Config

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_AUDIO = 1

# Callback patterns
CHECK_AUDIO_SUBSCRIPTION_PATTERN = "^check_audio_subscription$"

class AudioToVoiceHandler:
    def __init__(self, config: Config):
        self.config = config
        self.temp_dir = Path(tempfile.gettempdir()) / "tgsecret_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Supported audio formats
        self.supported_formats = {
            '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', 
            '.wma', '.opus', '.mp4', '.avi', '.mov', '.mkv'
        }

    async def start_audio_conversion(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start audio to voice conversion process"""
        user_id = update.effective_user.id
        
        # Check subscription first (for all users except owner)
        if user_id != self.config.OWNER_ID:
            from bot.handlers import check_subscription
            is_subscribed, missing_channels = await check_subscription(context.bot, user_id)
            if not is_subscribed and missing_channels:
                # Create custom keyboard for audio converter
                keyboard = []
                for channel in missing_channels:
                    if channel.startswith('@'):
                        channel_link = f"https://t.me/{channel[1:]}"
                        button_text = f"📢 {channel}"
                    else:
                        channel_link = channel
                        button_text = "📢 Kanalga o'tish"
                    keyboard.append([InlineKeyboardButton(button_text, url=channel_link)])
                
                # Add custom check button for audio converter
                keyboard.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_audio_subscription")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "🔒 Audio to Voice funksiyasidan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
                    reply_markup=reply_markup
                )
                return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_audio_conversion")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎵 <b>Audio to Voice Converter</b>\n\n"
            "📎 Audio fayl yuboring (mp3, wav, ogg, m4a, aac, flac, wma, opus)\n"
            "📹 Yoki video fayl yuboring (mp4, avi, mov, mkv)\n\n"
            "⚡ Bot audio ni ovozli habarga aylantiradi",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_AUDIO

    async def handle_audio_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle received audio file"""
        user_id = update.effective_user.id
        
        # Check subscription
        if not await self._check_user_subscription(update, context, user_id):
            return ConversationHandler.END
        
        # Get and validate file
        file_info = await self._get_and_validate_file(update)
        if not file_info:
            return WAITING_FOR_AUDIO
            
        file_obj, file_name, file_size = file_info
        
        # Process the file
        return await self._process_audio_file(update, context, file_obj, file_name, file_size)

    async def _check_user_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
        """Check if user has subscription (owner always allowed)"""
        if user_id != self.config.OWNER_ID:
            from bot.handlers import check_subscription, get_subscription_keyboard
            is_subscribed, missing_channels = await check_subscription(context.bot, user_id)
            if not is_subscribed and missing_channels:
                keyboard = get_subscription_keyboard(missing_channels)
                await update.message.reply_text(
                    "🔒 Iltimos, avval kanallarga obuna bo'ling:",
                    reply_markup=keyboard
                )
                return False
        return True

    async def _get_and_validate_file(self, update: Update) -> tuple:
        """Get file info and validate format/size"""
        file_obj, file_name, file_size = self._extract_file_info(update)
        
        if not file_obj:
            await update.message.reply_text(
                "❌ Audio yoki video fayl yuboring!\n\n"
                "📎 Quyidagi formatlarni qo'llab-quvvatlayman:\n"
                "🎵 Audio: mp3, wav, ogg, m4a, aac, flac, wma, opus\n"
                "📹 Video: mp4, avi, mov, mkv"
            )
            return None
            
        # Check file size (max 50MB)
        if file_size and file_size > 50 * 1024 * 1024:
            await update.message.reply_text(
                "❌ Fayl hajmi juda katta!\n"
                "📏 Maksimal hajm: 50MB"
            )
            return None
            
        return file_obj, file_name, file_size

    def _extract_file_info(self, update: Update) -> tuple:
        """Extract file object, name and size from update"""
        if update.message.audio:
            file_obj = update.message.audio
            file_name = file_obj.file_name or f"audio_{file_obj.file_id}.mp3"
            file_size = file_obj.file_size
        elif update.message.voice:
            file_obj = update.message.voice
            file_name = f"voice_{file_obj.file_id}.ogg"
            file_size = file_obj.file_size
        elif update.message.video_note:
            file_obj = update.message.video_note
            file_name = f"video_note_{file_obj.file_id}.mp4"
            file_size = file_obj.file_size
        elif update.message.video:
            file_obj = update.message.video
            file_name = file_obj.file_name or f"video_{file_obj.file_id}.mp4"
            file_size = file_obj.file_size
        elif update.message.document:
            file_obj = update.message.document
            file_name = file_obj.file_name or f"document_{file_obj.file_id}"
            file_size = file_obj.file_size
            
            # Check if document is audio/video
            if not self._is_supported_format(file_name):
                return None, None, None
        else:
            return None, None, None
            
        return file_obj, file_name, file_size

    async def _process_audio_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 file_obj, file_name: str, file_size: int) -> int:
        """Process the audio file conversion"""
        # Send processing message
        processing_msg = await update.message.reply_text(
            "⏳ Audio ishlanmoqda...\n"
            f"� Fayl: {file_name}\n"
            f"📏 Hajm: {self._format_file_size(file_size)}"
        )
        
        try:
            # Download and convert
            await self._download_and_convert(context, file_obj, file_name, processing_msg, update)
            
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            await processing_msg.edit_text(
                "❌ Audio konvertatsiya qilishda xatolik yuz berdi!\n\n"
                "� Sabablari:\n"
                "• Fayl buzuq bo'lishi mumkin\n"
                "• Qo'llab-quvvatlanmaydigan format\n"
                "• Server xatosi\n\n"
                "🔄 Boshqa fayl bilan qayta urinib ko'ring"
            )
        finally:
            # Clean up temporary files
            self._cleanup_temp_files(file_obj.file_id)
        
        return WAITING_FOR_AUDIO

    async def _download_and_convert(self, context, file_obj, file_name: str, processing_msg, update):
        """Download file and convert to voice message"""
        # Download file
        file = await context.bot.get_file(file_obj.file_id)
        input_path = self.temp_dir / f"input_{file_obj.file_id}_{file_name}"
        await file.download_to_drive(input_path)
        
        # Convert to voice message format
        output_path = await self._convert_to_voice(input_path, file_obj.file_id)
        
        if not output_path or not output_path.exists():
            raise RuntimeError("Konvertatsiya xatosi")
        
        # Update processing message
        await processing_msg.edit_text("📤 Ovozli habar yuborilmoqda...")
        
        # Send as voice message
        import aiofiles
        async with aiofiles.open(output_path, 'rb') as voice_file:
            voice_data = await voice_file.read()
            await update.message.reply_voice(
                voice=voice_data,
                caption=f"🎵 Konvertatsiya qilingan audio\n📁 Asl fayl: {file_name}"
            )
        
        # Delete processing message and send success
        await processing_msg.delete()
        await update.message.reply_text(
            "✅ Audio muvaffaqiyatli ovozli habarga aylantirildi!\n\n"
            "🔄 Yana audio yuborish uchun fayl yuboring\n"
            "❌ Chiqish uchun /cancel"
        )

    async def cancel_conversion(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel audio conversion"""
        query = update.callback_query
        
        if query:
            await query.answer()
            await query.edit_message_text(
                "❌ Audio konvertatsiya bekor qilindi"
            )
        else:
            # If called via /cancel command
            await update.message.reply_text(
                "❌ Audio konvertatsiya bekor qilindi"
            )
        
        return ConversationHandler.END

    async def check_audio_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Check subscription for audio converter and restart if subscribed"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        from bot.handlers import check_subscription
        is_subscribed, _ = await check_subscription(context.bot, user_id)
        
        if is_subscribed:
            # User is now subscribed, restart audio conversion
            await query.edit_message_text(
                "✅ Obuna tasdiqlandi! Endi audio fayl yuboring."
            )
            # Start the audio conversion process
            keyboard = [
                [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_audio_conversion")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "🎵 <b>Audio to Voice Converter</b>\n\n"
                "📎 Audio fayl yuboring (mp3, wav, ogg, m4a, aac, flac, wma, opus)\n"
                "📹 Yoki video fayl yuboring (mp4, avi, mov, mkv)\n\n"
                "⚡ Bot audio ni ovozli habarga aylantiradi",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return WAITING_FOR_AUDIO
        else:
            # Still not subscribed
            await query.edit_message_text(
                "❌ Hali ham barcha kanallarga obuna bo'lmagansiz.\n"
                "Iltimos, barcha kanallarga obuna bo'ling va qayta urinib ko'ring."
            )
            return ConversationHandler.END

    async def _convert_to_voice(self, input_path: Path, file_id: str) -> Optional[Path]:
        """Convert audio file to voice message format using FFmpeg"""
        output_path = self.temp_dir / f"voice_{file_id}.ogg"
        
        try:
            # FFmpeg command for voice message conversion
            # Convert to OGG Opus format (Telegram voice message format)
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-c:a', 'libopus',           # Opus codec
                '-b:a', '64k',               # 64kbps bitrate
                '-ar', '48000',              # 48kHz sample rate
                '-ac', '1',                  # Mono channel
                '-application', 'voip',      # VoIP application (optimized for voice)
                '-f', 'ogg',                 # OGG container
                '-y',                        # Overwrite output file
                str(output_path)
            ]
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            _, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"FFmpeg error: {stderr.decode()}")
                return None
            
            return output_path
            
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return None

    def _is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported"""
        if not filename:
            return False
        
        file_ext = Path(filename).suffix.lower()
        return file_ext in self.supported_formats

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if not size_bytes:
            return "Noma'lum"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _cleanup_temp_files(self, file_id: str):
        """Clean up temporary files"""
        try:
            # Remove input and output files
            for pattern in [f"input_{file_id}_*", f"voice_{file_id}.*"]:
                for temp_file in self.temp_dir.glob(pattern):
                    if temp_file.exists():
                        temp_file.unlink()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def get_audio_to_voice_handler(config: Config) -> ConversationHandler:
    """Get audio to voice conversion handler"""
    handler = AudioToVoiceHandler(config)
    
    return ConversationHandler(
        entry_points=[
            CommandHandler("audio2voice", handler.start_audio_conversion),
            CallbackQueryHandler(handler.check_audio_subscription, pattern=CHECK_AUDIO_SUBSCRIPTION_PATTERN),
        ],
        states={
            WAITING_FOR_AUDIO: [
                MessageHandler(
                    filters.AUDIO | filters.VOICE | filters.VIDEO_NOTE | 
                    filters.VIDEO | filters.Document.ALL,
                    handler.handle_audio_file
                ),
                CallbackQueryHandler(handler.cancel_conversion, pattern="^cancel_audio_conversion$"),
                CallbackQueryHandler(handler.check_audio_subscription, pattern=CHECK_AUDIO_SUBSCRIPTION_PATTERN),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", handler.cancel_conversion),
            CallbackQueryHandler(handler.cancel_conversion, pattern="^cancel_audio_conversion$"),
            CallbackQueryHandler(handler.check_audio_subscription, pattern=CHECK_AUDIO_SUBSCRIPTION_PATTERN),
        ],
        per_message=False,
        per_chat=True,
        per_user=True,
    )
