"""
Main entry point for the Telethon Userbot project.
Runs both the login bot and userbot together.
- Login bot handles session creation via Telegram (open to all users)
- Each user gets their own userbot session
"""

import os
import sys
import asyncio
import logging
import glob

# Ensure we're in the project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import config
from bot.handlers import (
    start_command,
    get_login_conversation_handler,
    get_audio_to_voice_handler,
    WELCOME_MESSAGE
)
from bot.keyboards import Keyboards
from bot.session_creator import get_user_session_path
from bot.transcribe_handler import transcribe_command, handle_audio_message
from bot.admin_commands import (
    cmd_admin_panel, cmd_set_channel, cmd_remove_channel, cmd_check_config,
    handle_admin_config, handle_admin_set_channel, handle_admin_remove_channel, handle_admin_refresh,
    handle_admin_channels_view, handle_admin_channels_manage, handle_admin_add_channel_info, 
    handle_admin_remove_channel_info, handle_channel_remove, handle_add_channel_message
)

# Configure logging - minimal output
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
logger = logging.getLogger(__name__)

# Sessions directory
SESSIONS_DIR = os.path.join(PROJECT_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Global reference to userbot tasks and clients (per user)
userbot_tasks: dict = {}
userbot_clients: dict = {}
userbot_start_times: dict = {}  # Track when each userbot started


async def run_userbot_for_user(user_id: int):
    """Run the userbot for a specific user."""
    from telethon import TelegramClient
    from userbot.loader import ModuleLoader
    from datetime import datetime, timedelta
    
    global userbot_clients, userbot_start_times
    
    session_path = get_user_session_path(user_id)
    session_name = session_path.replace('.session', '')
    
    if not os.path.exists(session_path):
        print("⏳ No session for user {}".format(user_id))
        return None
    
    print("🚀 Starting Userbot for user {}...".format(user_id))
    
    client = TelegramClient(
        session_name,
        config.API_ID,
        config.API_HASH,
        device_model="Desktop",
        system_version="Windows 10",
        app_version="Userbot 1.0",
        lang_code="en"
    )
    
    # Store client reference and start time
    userbot_clients[user_id] = client
    userbot_start_times[user_id] = datetime.now()
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"❌ Session not authorized for user {user_id}")
            print(f"   Session file: {session_path}")
            # Delete invalid session
            try:
                await client.disconnect()
                del userbot_clients[user_id]
                os.remove(session_path)
                print("   Deleted invalid session file")
            except OSError as e:
                print("   Could not delete session: {}".format(e))
            return None
        
        me = await client.get_me()
        sleep_hours = config.AUTO_SLEEP_HOURS
        sleep_info = f" (uxlash: {sleep_hours} soatdan keyin)" if sleep_hours > 0 else ""
        print(f"✅ Userbot for {me.first_name} (@{me.username or 'N/A'}) - ID: {me.id}{sleep_info}")
        
        # Load modules (each user gets their own module instance)
        loader = ModuleLoader(client, me.id)
        loaded = loader.load_all_modules()
        print(f"📦 Loaded {loaded} module(s) for user {me.id}")
        
        # Auto-sleep logic
        if sleep_hours > 0:
            sleep_time = sleep_hours * 3600  # Convert to seconds
            
            async def auto_sleep_timer():
                await asyncio.sleep(sleep_time)
                print(f"😴 Auto-sleep: Userbot for user {user_id} going to sleep after {sleep_hours} hours")
                if client.is_connected():
                    await client.disconnect()
            
            # Start auto-sleep timer in background
            sleep_task = asyncio.create_task(auto_sleep_timer())
            # Keep reference to prevent garbage collection
            sleep_task.add_done_callback(lambda t: None)
        
        # Run until disconnected
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Userbot error for user {user_id}: {e}")
    finally:
        if client and client.is_connected():
            await client.disconnect()
        if user_id in userbot_clients:
            del userbot_clients[user_id]
        if user_id in userbot_start_times:
            del userbot_start_times[user_id]


async def start_userbot_for_user_background(user_id: int):
    """Start userbot for a specific user in background."""
    global userbot_tasks, userbot_clients
    
    # Check if already running
    if user_id in userbot_tasks and not userbot_tasks[user_id].done():
        print(f"⚠️ Userbot for user {user_id} already running, skipping...")
        return
    
    # First disconnect client if exists
    if user_id in userbot_clients:
        try:
            client = userbot_clients[user_id]
            if client.is_connected():
                await client.disconnect()
            del userbot_clients[user_id]
        except Exception:
            pass
        await asyncio.sleep(1)  # Wait for resources to be released
    
    # Start new userbot task for this user
    userbot_tasks[user_id] = asyncio.create_task(run_userbot_for_user(user_id))


async def post_init(application: Application):
    """Called after the bot is initialized. Start all existing user sessions."""
    # Find all session files
    session_files = glob.glob(os.path.join(SESSIONS_DIR, "session_*.session"))
    
    if session_files:
        print(f"📁 Found {len(session_files)} existing session(s)")
        for session_file in session_files:
            # Extract user_id from filename (session_123456.session)
            filename = os.path.basename(session_file)
            try:
                user_id = int(filename.replace("session_", "").replace(".session", ""))
                await start_userbot_for_user_background(user_id)
                await asyncio.sleep(2)  # Delay between starting userbots
            except ValueError:
                continue
    else:
        print("⏳ No existing sessions. Users can create sessions via the bot.")


async def main():
    """Main async entry point."""
    print("=" * 50)
    print("🤖 Telethon Userbot System")
    print("=" * 50)
    print(f"Owner ID: {config.OWNER_ID}")
    print("=" * 50)
    
    # Create bot application
    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("transcribe", transcribe_command))
    
    # Admin commands (OWNER only)
    application.add_handler(CommandHandler("admin", cmd_admin_panel))
    application.add_handler(CommandHandler("setchannel", cmd_set_channel))
    application.add_handler(CommandHandler("removechannel", cmd_remove_channel))
    application.add_handler(CommandHandler("config", cmd_check_config))
    
    application.add_handler(get_login_conversation_handler())
    application.add_handler(
        CallbackQueryHandler(handle_start_userbot, pattern="^start_userbot$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_wakeup_userbot, pattern="^wakeup_userbot$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_check_status, pattern="^check_status$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_logout, pattern="^logout$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_check_subscription, pattern="^check_subscription$")
    )
    
    # Admin panel callbacks (OWNER only)
    application.add_handler(
        CallbackQueryHandler(handle_admin_config, pattern="^admin_config$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_channels_view, pattern="^admin_channels_view")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_channels_manage, pattern="^admin_channels_manage")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_add_channel_info, pattern="^admin_add_channel_info$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_remove_channel_info, pattern="^admin_remove_channel_info$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_set_channel, pattern="^admin_set_channel$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_remove_channel, pattern="^admin_remove_channel$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_channel_remove, pattern="^remove_channel_")
    )
    application.add_handler(
        CallbackQueryHandler(handle_admin_refresh, pattern="^admin_refresh$")
    )
    
    # Admin text message handler for adding channels (OWNER only)
    application.add_handler(
        MessageHandler(filters.TEXT & filters.User(config.OWNER_ID) & ~filters.COMMAND, handle_add_channel_message)
    )
    
    # Audio to voice conversion handler
    application.add_handler(get_audio_to_voice_handler(config))
    
    # Audio transcription handler (for audio/voice messages)
    application.add_handler(
        MessageHandler(
            filters.AUDIO | filters.VOICE | filters.VIDEO | filters.VIDEO_NOTE | 
            (filters.Document.AUDIO | filters.Document.VIDEO),
            handle_audio_message
        )
    )
    
    print("✅ Login Bot is running!")
    print("👉 Open Telegram and message your bot to login")
    print("=" * 50)
    
    # Start polling
    await application.initialize()
    await application.start()
    
    # Set menu button after bot starts
    try:
        from telegram import BotCommand, MenuButtonCommands
        commands = [
            BotCommand("start", "Botni ishga tushirish va boshqaruv paneli"),
            BotCommand("help", "Bot haqida ma'lumot va yordam"),
            BotCommand("transcribe", "Audio/voice ni matnga aylantirish (Whisper AI)"),
            BotCommand("audio2voice", "Audio faylni ovozli habarga aylantirish (FFmpeg)")
        ]
        await application.bot.set_my_commands(commands)
        await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        print("✅ Menu button sozlandi!")
    except Exception as e:
        print(f"⚠️ Menu button xatosi: {e}")
    
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("\n👋 Shutting down...")
        # Cancel all userbot tasks
        for user_id, task in userbot_tasks.items():
            if task and not task.done():
                task.cancel()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        raise


async def help_command(update: Update, context):
    """Handle /help command - show bot information and usage."""
    help_text = """
🤖 **Telethon Userbot Boshqaruv Tizimi**

**Bot haqida:**
Bu bot sizning Telegram akkauntingizga userbot ulash va boshqarish imkonini beradi. Userbot - bu sizning akkauntingiz orqali ishlaydigan va turli buyruqlarni bajaradigan maxsus dastur.

**Asosiy imkoniyatlar:**
• Akkauntni xavfsiz ulash (2FA qo'llab-quvvatlash bilan)
• Userbotni ishga tushirish va boshqarish
• Medialarni saqlash (.ok buyrug'i)
• AI bilan suhbat (.ask buyrug'i)
• Audio/voice transkript (bot va userbot)
• Avtomatik uxlash rejimi

**Qanday foydalanish:**

1️⃣ **Akkaunt ulash:**
   • /start buyrug'ini yuboring
   • "🔗 Akkaunt ulash" tugmasini bosing
   • Telefon raqamingizni kiriting
   • Telegram'dan kelgan kodni kiriting
   • Agar 2FA yoqilgan bo'lsa, parolingizni kiriting

2️⃣ **Userbotni ishga tushirish:**
   • Akkaunt ulanganidan keyin
   • "🚀 Userbot ishga tushirish" tugmasini bosing
   • Userbot fonda ishlaydi

3️⃣ **Userbot buyruqlari:**
   • `.ok` - Mediaga javob berib saqlash (Saqlangan Xabarlarga)
   • `.ask <savol>` - AI dan so'rash (javob o'sha chatda)
   • `.transcribe` - Audio/voice/video ni matnga (Whisper AI)
   • `.help` - Barcha buyruqlarni ko'rish

4️⃣ **Bot buyruqlari:**
   • /transcribe - Audio transkript ma'lumotini olish
   • Audio yuborish - Botga to'g'ridan-to'g'ri audio/voice yuborsangiz avtomatik matnga aylanadi

**Xavfsizlik:**
✅ Faqat siz o'z userbotingizni boshqarasiz
✅ Buyruqlar avtomatik o'chiriladi
✅ `.ok` javoblari Saqlangan Xabarlarga boradi

**Yordam kerakmi?**
Muammo bo'lsa, /start bosib qaytadan urinib ko'ring.
"""
    
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_start_userbot(update: Update, context):
    """Handle start userbot button - starts userbot for this user."""
    from bot.handlers import check_subscription, get_subscription_keyboard
    
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check subscription
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
    
    session_path = get_user_session_path(user_id)
    
    if not os.path.exists(session_path):
        await query.message.reply_text(
            "❌ Sessiya topilmadi! Avval 'Akkaunt ulash' orqali kiring.",
        )
        return
    
    await query.edit_message_text("🚀 Userbot ishga tushirilmoqda...")
    
    # Start userbot for this user
    await start_userbot_for_user_background(user_id)
    
    await query.message.reply_text(
        "✅ **Userbotingiz ishlamoqda!**\n\n"
        "📱 **Buyruqlar:**\n"
        "• `.ok` - Media saqlash\n"
        "• `.ask <savol>` - AI suhbat\n"
        "• `.transcribe` - Audio → Text\n"
        "• `.help` - To'liq qo'llanma\n\n"
        "🎙️ **Whisper AI:** Har qanday til, har qanday format",
        parse_mode="Markdown"
    )


async def handle_wakeup_userbot(update: Update, context):
    """Handle wake up button - restarts the userbot for this user."""
    from bot.handlers import check_subscription, get_subscription_keyboard
    
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check subscription
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
    
    session_path = get_user_session_path(user_id)
    
    if not os.path.exists(session_path):
        await query.message.reply_text("❌ Sessiya topilmadi! Avval akkaunt ulang.")
        return
    
    await query.edit_message_text("⏰ Userbot qayta ishga tushirilmoqda...")
    
    global userbot_tasks
    
    # Cancel existing task for this user
    if user_id in userbot_tasks and not userbot_tasks[user_id].done():
        userbot_tasks[user_id].cancel()
        try:
            await userbot_tasks[user_id]
        except asyncio.CancelledError:
            # Task was cancelled successfully, continue with cleanup
            print(f"✅ Userbot task for user {user_id} cancelled successfully")
        await asyncio.sleep(1)
    
    # Start fresh for this user
    await start_userbot_for_user_background(user_id)
    
    await query.message.reply_text(
        "✅ **Userbotingiz qayta ishladi!**\n\n"
        "Endi ishlashi kerak.\n"
        "Sinash uchun `.help` yozing.",
        parse_mode="Markdown"
    )


async def handle_check_status(update: Update, context):
    """Handle status check button for this user."""
    from bot.handlers import check_subscription, get_subscription_keyboard
    
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check subscription
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
    
    session_path = get_user_session_path(user_id)
    session_exists = os.path.exists(session_path)
    
    global userbot_tasks
    userbot_running = user_id in userbot_tasks and not userbot_tasks[user_id].done()
    
    status_text = f"""
📊 **Sizning holatizgiz**

**Sessiya:** {'✅ Mavjud' if session_exists else '❌ Topilmadi'}
**Userbot:** {'🟢 Ishlayapti' if userbot_running else '🔴 To\'xtagan'}

{'Qayta ishga tushirish uchun "Qayta ishga tushirish" tugmasini bosing.' if session_exists and not userbot_running else ''}
{'Sessiya yaratish uchun "Akkaunt ulash" tugmasini bosing.' if not session_exists else ''}
"""
    
    try:
        await query.edit_message_text(
            status_text,
            parse_mode="Markdown",
            reply_markup=query.message.reply_markup
        )
    except Exception as e:
        if "not modified" not in str(e).lower():
            raise


async def handle_check_subscription(update: Update, context):
    """Handle subscription check callback."""
    from bot.handlers import check_subscription, get_subscription_keyboard
    from telegram.error import BadRequest
    
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check all required channels
    is_subscribed, missing_channels = await check_subscription(context.bot, user_id)
    
    try:
        if is_subscribed:
            # User is subscribed to all channels
            await query.edit_message_text(
                "✅ <b>Obuna tasdiqlandi!</b>\n\n" + WELCOME_MESSAGE,
                parse_mode="HTML",
                reply_markup=Keyboards.main_menu_keyboard()
            )
        else:
            # User is missing some channels
            channels_text = "\n".join([f"• {ch}" for ch in missing_channels])
            await query.edit_message_text(
                f"❌ <b>Siz hali obuna bo'lmagansiz!</b>\n\n"
                f"Iltimos, avval kanallarga obuna bo'ling:\n\n"
                f"{channels_text}",
                parse_mode="HTML",
                reply_markup=get_subscription_keyboard(missing_channels)
            )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise


async def handle_logout(update: Update, context):
    """Handle logout button - removes user session completely."""
    from bot.handlers import check_subscription, get_subscription_keyboard
    
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check subscription
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
    
    session_path = get_user_session_path(user_id)
    
    global userbot_tasks, userbot_clients
    
    await query.edit_message_text("⏳ Chiqish amalga oshirilmoqda...")
    
    # First disconnect the client if it exists
    if user_id in userbot_clients:
        try:
            client = userbot_clients[user_id]
            if client.is_connected():
                await client.disconnect()
            del userbot_clients[user_id]
        except Exception:
            pass
    
    # Then cancel the task
    if user_id in userbot_tasks:
        try:
            userbot_tasks[user_id].cancel()
            await asyncio.sleep(1)  # Wait for task to finish
        except Exception:
            pass
        if user_id in userbot_tasks:
            del userbot_tasks[user_id]
    
    # Wait a bit for file to be released
    await asyncio.sleep(1)
    
    # Delete session file
    if os.path.exists(session_path):
        try:
            os.remove(session_path)
            await query.message.reply_text(
                "✅ **Muvaffaqiyatli chiqildi!**\n\n"
                "Sizning sessiyangiz o'chirildi.\n"
                "Qayta ulash uchun /start bosing.",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.message.reply_text(
                f"❌ Sessiyani o'chirishda xatolik: {e}\n\n"
                "Iltimos, botni qayta ishga tushiring va qaytadan urinib ko'ring.",
            )
    else:
        await query.message.reply_text(
            "⚠️ Sessiya topilmadi.\n\n"
            "Akkaunt ulash uchun /start bosing.",
        )


if __name__ == "__main__":
    # Validate configuration
    if not config.validate():
        print("❌ Configuration error! Check your .env file.")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped by user.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
