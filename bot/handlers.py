"""
Handler module for the Telegram login bot.
Contains all message and callback handlers for the login flow.
"""

import os
import sys
import asyncio
import subprocess
from enum import Enum, auto
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from bot.keyboards import Keyboards
from bot.session_creator import get_session_creator, remove_session_creator
from bot.audio_to_voice_handler import get_audio_to_voice_handler


class LoginState(Enum):
    """States for the login conversation flow."""
    WAITING_PHONE = auto()
    WAITING_CODE = auto()
    WAITING_2FA = auto()


async def check_subscription(bot, user_id: int) -> tuple:
    """Check if user is subscribed to ALL required channels.
    Returns: (is_subscribed: bool, missing_channels: list or None)
    """
    # Reload channels to get latest
    config.reload_channels()
    channels = config.get_required_channels()
    
    if not channels:
        return True, None  # No channels configured, allow all
    
    missing_channels = []
    bot_errors = []
    
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            is_member = member.status in ['member', 'administrator', 'creator']
            if not is_member:
                missing_channels.append(channel)
        except Exception as e:
            error_str = str(e).lower()
            print(f"⚠️ Obuna tekshiruvi xatosi: {e}")
            if "chat not found" in error_str or "chat_not_found" in error_str:
                bot_errors.append(channel)
            elif "not enough rights" in error_str or "administrator" in error_str:
                bot_errors.append(channel)
            else:
                # Unknown error - don't block user
                pass
    
    # If bot has errors, show them but don't block
    if bot_errors:
        print(f"⚠️ Obuna tekshiruvi: bot_not_in_channel - {','.join(bot_errors)}")
        return True, None
    
    # User must be subscribed to ALL channels
    if missing_channels:
        return False, missing_channels
    
    return True, None


def get_subscription_keyboard(missing_channels=None):
    """Create keyboard with subscription buttons for all channels."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Get all channels or use provided missing channels
    if missing_channels is None:
        config.reload_channels()
        channels = config.get_required_channels()
    else:
        channels = missing_channels
    
    keyboard = []
    
    # Add button for each channel
    for channel in channels:
        if channel.startswith('-100'):
            # Private channel ID - can't create direct link easily
            channel_link = f"https://t.me/c/{channel[4:]}"
            button_text = f"📢 Kanal {channel[:10]}..."
        else:
            # Public channel username
            channel_link = f"https://t.me/{channel.replace('@', '')}"
            button_text = f"📢 {channel}"
        
        keyboard.append([InlineKeyboardButton(button_text, url=channel_link)])
    
    # Add check button
    keyboard.append([InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription")])
    
    return InlineKeyboardMarkup(keyboard)


# Welcome message shown on /start
WELCOME_MESSAGE = """
🤖 **Userbot Boshqaruv Paneli**

**Mavjud amallar:**
🔗 **Akkaunt ulash** - Telegram akkauntingizni ulang
🚀 **Ishga tushirish** - Userbotni yoqish
⏰ **Qayta ishga tushirish** - Userbot to'xtasa qayta yoqish
📊 **Holat** - Userbot holatini tekshirish
🚪 **Chiqish** - Akkauntni uzish va sessiyani o'chirish
"""

PHONE_REQUEST_MESSAGE = """
📱 **Telefon raqamingizni kiriting**

Telefon raqamingizni xalqaro formatda kiriting.

**Misol:** `+998901234567`

Davlat kodini `+` belgisi bilan kiriting.
"""

CODE_REQUEST_MESSAGE = """
🔢 **Tasdiqlash kodini kiriting**

Telegram sizga kod yubordi.
Kodni quyidagi formatda kiriting:

**Misol:** `4 2 1 9 8`

(Har bir raqam orasida bo'sh joy bilan)
"""

PASSWORD_REQUEST_MESSAGE = """
🔐 **Ikki bosqichli autentifikatsiya**

Akkauntingizda 2FA yoqilgan.
Iltimos, 2FA parolingizni kiriting.
"""


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    Shows welcome message with control panel.
    """
    user_id = update.effective_user.id
    
    # Check subscription for all required channels
    is_subscribed, missing_channels = await check_subscription(context.bot, user_id)
    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        await update.message.reply_text(
            f"⚠️ <b>Obuna talab qilinadi!</b>\n\n"
            f"Botdan foydalanish uchun avval kanallarga obuna bo'ling:\n\n"
            f"{channels_text}\n\n"
            f"Obuna bo'lgandan so'ng \"✅ Obunani tekshirish\" tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(missing_channels)
        )
        return
    
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=Keyboards.main_menu_keyboard()
    )


async def connect_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle 'Connect Account' button callback.
    Starts the login flow by asking for phone number.
    """
    query = update.callback_query
    await query.answer()
    
    # Check subscription for all required channels
    user_id = update.effective_user.id
    is_subscribed, missing_channels = await check_subscription(context.bot, user_id)
    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        await query.edit_message_text(
            f"⚠️ <b>Obuna talab qilinadi!</b>\n\n"
            f"Botdan foydalanish uchun avval kanallarga obuna bo'ling:\n\n"
            f"{channels_text}\n\n"
            f"Obuna bo'lgandan so'ng \"✅ Obunani tekshirish\" tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(missing_channels)
        )
        return ConversationHandler.END
    
    # Initialize session creator for this user
    session_creator = get_session_creator(user_id)
    
    # Check if session already exists
    if session_creator.session_exists():
        await query.edit_message_text(
            "⚠️ <b>Mavjud sessiya topildi!</b>\n\n"
            "Sessiya fayli allaqachon mavjud. Davom etsangiz yangi sessiya yaratiladi.\n"
            "Eski sessiya almashtiriladi.",
            parse_mode="HTML"
        )
    
    await query.message.reply_text(
        PHONE_REQUEST_MESSAGE,
        parse_mode="Markdown",
        reply_markup=Keyboards.cancel_keyboard()
    )
    
    return LoginState.WAITING_PHONE.value


async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle phone number input.
    Sends verification code request to Telegram.
    """
    user_id = update.effective_user.id
    phone_number = update.message.text.strip()
    
    # Send processing message
    await update.message.reply_text(
        "⏳ Sending verification code...",
        reply_markup=Keyboards.remove_keyboard()
    )
    
    # Get session creator and start login
    session_creator = get_session_creator(user_id)
    success, message = await session_creator.start_login(phone_number)
    
    if success:
        await update.message.reply_text(
            CODE_REQUEST_MESSAGE,
            parse_mode="Markdown",
            reply_markup=Keyboards.cancel_keyboard()
        )
        return LoginState.WAITING_CODE.value
    else:
        await update.message.reply_text(
            message,
            reply_markup=Keyboards.retry_keyboard()
        )
        remove_session_creator(user_id)
        return ConversationHandler.END


async def code_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle verification code input.
    Attempts to sign in with the code.
    """
    user_id = update.effective_user.id
    code = update.message.text.strip()
    
    # Send processing message
    await update.message.reply_text("⏳ Verifying code...")
    
    # Verify the code
    session_creator = get_session_creator(user_id)
    success, message, needs_2fa = await session_creator.verify_code(code)
    
    if needs_2fa:
        # 2FA required
        await update.message.reply_text(
            PASSWORD_REQUEST_MESSAGE,
            parse_mode="Markdown",
            reply_markup=Keyboards.cancel_keyboard()
        )
        return LoginState.WAITING_2FA.value
    elif success:
        # Login successful
        user_info = await session_creator.get_user_info()
        # Build name safely (last_name might be None)
        full_name = user_info['first_name']
        if user_info.get('last_name'):
            full_name += f" {user_info['last_name']}"
        
        success_message = (
            "✅ Muvaffaqiyatli!\n\n"
            "Akkaunt ma'lumotlari:\n"
            f"👤 Ism: {full_name}\n"
            f"🆔 ID: {user_info['id']}\n"
            f"📱 Telefon: +{user_info['phone']}\n\n"
            "Sessiya yaratildi!\n"
            "Endi userbotni ishga tushirishingiz mumkin."
        )
        await update.message.reply_text(
            success_message,
            reply_markup=Keyboards.success_keyboard()
        )
        
        # Disconnect the client (session is saved)
        await session_creator.disconnect()
        remove_session_creator(user_id)
        return ConversationHandler.END
    else:
        # Login failed
        await update.message.reply_text(
            message,
            reply_markup=Keyboards.retry_keyboard()
        )
        
        if "expired" in message.lower():
            await session_creator.disconnect()
            remove_session_creator(user_id)
            return ConversationHandler.END
        
        # Allow retry for invalid code
        return LoginState.WAITING_CODE.value


async def password_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle 2FA password input.
    Attempts to complete sign in with the password.
    """
    user_id = update.effective_user.id
    password = update.message.text.strip()
    
    # Send processing message
    await update.message.reply_text("⏳ Verifying password...")
    
    # Verify 2FA password
    session_creator = get_session_creator(user_id)
    success, message = await session_creator.verify_2fa(password)
    
    if success:
        # Login successful
        user_info = await session_creator.get_user_info()
        # Build name safely (last_name might be None)
        full_name = user_info['first_name']
        if user_info.get('last_name'):
            full_name += f" {user_info['last_name']}"
        
        success_message = (
            "✅ 2FA bilan muvaffaqiyatli!\n\n"
            "Akkaunt ma'lumotlari:\n"
            f"👤 Ism: {full_name}\n"
            f"🆔 ID: {user_info['id']}\n"
            f"📱 Telefon: +{user_info['phone']}\n\n"
            "Sessiya yaratildi!\n"
            "Endi userbotni ishga tushirishingiz mumkin."
        )
        await update.message.reply_text(
            success_message,
            reply_markup=Keyboards.success_keyboard()
        )
        
        # Disconnect the client (session is saved)
        await session_creator.disconnect()
        remove_session_creator(user_id)
        return ConversationHandler.END
    else:
        # Password verification failed - allow retry
        await update.message.reply_text(
            f"{message}\n\nPlease try again or cancel.",
            reply_markup=Keyboards.cancel_keyboard()
        )
        return LoginState.WAITING_2FA.value


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle cancel button callback.
    Aborts the login process and cleans up.
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Cleanup session creator
    session_creator = get_session_creator(user_id)
    await session_creator.disconnect()
    remove_session_creator(user_id)
    
    await query.edit_message_text(
        "❌ **Bekor qilindi.**\n\nQaytadan urinish uchun /start bosing.",
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END


async def start_userbot_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle 'Start Userbot' button callback.
    Launches the userbot process.
    """
    query = update.callback_query
    await query.answer()
    
    if not await check_owner(update):
        await query.edit_message_text("⛔ Access denied.")
        return
    
    # Check subscription for all required channels
    user_id = update.effective_user.id
    is_subscribed, missing_channels = await check_subscription(context.bot, user_id)
    if not is_subscribed:
        channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
        await query.edit_message_text(
            f"⚠️ <b>Obuna talab qilinadi!</b>\n\n"
            f"Botdan foydalanish uchun avval kanallarga obuna bo'ling:\n\n"
            f"{channels_text}\n\n"
            f"Obuna bo'lgandan so'ng \"✅ Obunani tekshirish\" tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=get_subscription_keyboard(missing_channels)
        )
        return
    
    await query.edit_message_text("🚀 Starting userbot...")
    
    # Get the path to the userbot main.py
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    userbot_path = os.path.join(project_root, "userbot", "main.py")
    
    # Check if session exists
    session_path = f"{config.SESSION_PATH}.session"
    if not os.path.exists(session_path):
        await query.message.reply_text(
            "❌ **No session found!**\n\n"
            "Please connect your account first.",
            parse_mode="Markdown",
            reply_markup=Keyboards.start_keyboard()
        )
        return
    
    try:
        # Start userbot as a separate process
        if sys.platform == "win32":
            await asyncio.create_subprocess_exec(
                sys.executable, userbot_path,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=project_root
            )
        else:
            await asyncio.create_subprocess_exec(
                sys.executable, userbot_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                cwd=project_root
            )
        
        await query.message.reply_text(
            "✅ **Userbot started successfully!**\n\n"
            "The userbot is now running in the background.\n"
            "Use `.help` in any chat to see available commands.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.message.reply_text(
            f"❌ **Failed to start userbot:**\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=Keyboards.retry_keyboard()
        )


async def cancel_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle cancel text message during conversation."""
    return await cancel_callback(update, context)


def get_login_conversation_handler() -> ConversationHandler:
    """
    Create and return the login conversation handler.
    Manages the entire login flow state machine.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(connect_callback, pattern="^connect_account$")
        ],
        states={
            LoginState.WAITING_PHONE.value: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_received),
            ],
            LoginState.WAITING_CODE.value: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, code_received),
            ],
            LoginState.WAITING_2FA.value: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, password_received),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
            CommandHandler("cancel", cancel_message),
        ],
        per_user=True,
        per_chat=True,
    )
