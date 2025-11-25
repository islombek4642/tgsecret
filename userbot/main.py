"""
Main entry point for the Telethon userbot.
Initializes the client, loads modules, and starts the event loop.
"""

import os
import sys
import asyncio
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthKeyError

from config import config
from userbot.loader import ModuleLoader


# Minimal logging to stay hidden
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
logger = logging.getLogger(__name__)


class Userbot:
    """
    Main userbot class.
    Manages the Telethon client and module loading.
    """
    
    def __init__(self):
        """Initialize the userbot."""
        self.client: TelegramClient = None
        self.loader: ModuleLoader = None
        self.me = None
        
    async def start(self):
        """
        Start the userbot.
        Connects to Telegram and loads all modules.
        """
        print("=" * 50)
        print("🤖 Telethon Userbot")
        print("=" * 50)
        
        # Check for session file
        session_path = f"{config.SESSION_PATH}.session"
        if not os.path.exists(session_path):
            print("❌ No session file found!")
            print("Please run the login bot first to create a session.")
            return False
        
        # Create client
        self.client = TelegramClient(
            config.SESSION_PATH,
            config.API_ID,
            config.API_HASH,
            device_model="Desktop",
            system_version="Windows 10",
            app_version="Userbot 1.0",
            lang_code="en"
        )
        
        try:
            # Connect and verify session
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                print("❌ Session is not authorized!")
                print("Please run the login bot to create a new session.")
                return False
            
            # Get self info
            self.me = await self.client.get_me()
            
            # Verify owner
            if self.me.id != config.OWNER_ID:
                print(f"⚠️ Warning: Logged in as {self.me.id}, but OWNER_ID is {config.OWNER_ID}")
                print("Commands will only work for the configured OWNER_ID.")
            
            print(f"✅ Logged in as: {self.me.first_name} (@{self.me.username or 'N/A'})")
            print(f"🆔 User ID: {self.me.id}")
            
        except AuthKeyError:
            print("❌ Invalid session! The session key is corrupted.")
            print("Please delete the session file and create a new one.")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        
        # Initialize module loader
        self.loader = ModuleLoader(self.client)
        
        # Load all modules
        loaded = self.loader.load_all_modules()
        print(f"📦 Loaded {loaded} module(s)")
        
        # List loaded modules
        for name, info in self.loader.get_all_modules().items():
            commands = ", ".join([f".{cmd}" for cmd in info.commands]) if info.commands else "No commands"
            print(f"   └─ {name}: {commands}")
        
        print("=" * 50)
        print("✅ Userbot is now running!")
        print("Use .help to see available commands.")
        print("Press Ctrl+C to stop.")
        print("=" * 50)
        
        return True
    
    async def run(self):
        """Run the userbot event loop."""
        if not await self.start():
            return
        
        try:
            # Run until disconnected
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            pass
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the userbot and cleanup."""
        print("\n👋 Stopping userbot...")
        if self.client:
            await self.client.disconnect()
        print("✅ Userbot stopped.")


def main():
    """Main entry point."""
    # Validate configuration
    if not config.API_ID or not config.API_HASH:
        print("❌ API_ID and API_HASH are required!")
        print("Please check your .env file.")
        sys.exit(1)
    
    if not config.OWNER_ID:
        print("❌ OWNER_ID is required!")
        print("Please check your .env file.")
        sys.exit(1)
    
    # Create and run userbot
    userbot = Userbot()
    
    try:
        asyncio.run(userbot.run())
    except KeyboardInterrupt:
        print("\n👋 Stopped by user.")
    except Exception as e:
        logger.error(f"Userbot error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
