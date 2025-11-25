"""
Configuration module for the Telethon Userbot project.
Loads all environment variables and provides configuration constants.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Main configuration class containing all settings."""
    
    # Telegram Bot Token (for the login bot)
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Telegram API credentials
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")
    
    # Groq API Key for AI features
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Owner's Telegram User ID (only this user can use commands)
    OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
    
    # Session file path
    SESSION_NAME: str = "session"
    SESSION_PATH: str = os.path.join(os.path.dirname(__file__), SESSION_NAME)
    
    # Groq AI Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"
    
    # Subscription Configuration (can be comma-separated for multiple channels)
    REQUIRED_CHANNEL: str = os.getenv("REQUIRED_CHANNEL", "")
    
    @classmethod
    def get_required_channels(cls) -> list:
        """Get list of required channels from comma-separated string."""
        # Reload from env to get latest value
        cls.reload_channels()
        if cls.REQUIRED_CHANNEL:
            return [ch.strip() for ch in cls.REQUIRED_CHANNEL.split(",") if ch.strip()]
        return []
    
    @classmethod
    def reload_channels(cls):
        """Reload REQUIRED_CHANNEL from environment"""
        import os
        from dotenv import load_dotenv
        load_dotenv(override=True)
        cls.REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")
    
    # Auto-sleep Configuration (in hours, 0 = disabled)
    AUTO_SLEEP_HOURS: int = int(os.getenv("AUTO_SLEEP_HOURS", "24"))
    
    # Command prefix
    CMD_PREFIX: str = "."
    
    # Auto-delete delay for help messages (in seconds)
    HELP_DELETE_DELAY: int = 15
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        required = [
            ("BOT_TOKEN", cls.BOT_TOKEN),
            ("API_ID", cls.API_ID),
            ("API_HASH", cls.API_HASH),
            ("OWNER_ID", cls.OWNER_ID),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            print(f"❌ Missing required configuration: {', '.join(missing)}")
            return False
        
        return True
    
    @classmethod
    def validate_groq(cls) -> bool:
        """Check if Groq API is configured."""
        return bool(cls.GROQ_API_KEY)


# Create a singleton instance
config = Config()
