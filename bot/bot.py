"""
Main Telegram Bot module for login and session management.
This bot provides a user-friendly interface to connect Telegram accounts
and create session files for the userbot.
"""

import os
import sys
import logging
import asyncio

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)

from config import config
from bot.handlers import (
    start_command,
    start_userbot_callback,
    get_login_conversation_handler,
)


# Configure logging - minimal output to avoid leaking info
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING  # Only show warnings and errors
)
logger = logging.getLogger(__name__)


def create_application() -> Application:
    """
    Create and configure the Telegram bot application.
    
    Returns:
        Configured Application instance
    """
    # Create application with bot token
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Add conversation handler for login flow
    application.add_handler(get_login_conversation_handler())
    
    # Add callback handler for starting userbot
    application.add_handler(
        CallbackQueryHandler(start_userbot_callback, pattern="^start_userbot$")
    )
    
    return application


async def run_bot():
    """Run the bot using async context manager."""
    application = create_application()
    
    # Initialize and start
    await application.initialize()
    await application.start()
    
    # Start polling
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    print("✅ Login bot is running! Press Ctrl+C to stop.")
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        # Cleanup
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


def main():
    """Main entry point for the bot."""
    # Validate configuration
    if not config.validate():
        print("❌ Configuration validation failed!")
        print("Please check your .env file and ensure all required variables are set.")
        sys.exit(1)
    
    print("=" * 50)
    print("🤖 Telegram Login Bot")
    print("=" * 50)
    print(f"Owner ID: {config.OWNER_ID}")
    print("=" * 50)
    
    try:
        # Run the bot
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        print(f"❌ Bot error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
