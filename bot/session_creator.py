"""
Session creator module using Telethon.
Handles the entire login flow: phone number, code verification, and 2FA.
Creates session files that can be used by the userbot.
"""

import os
import sys
import asyncio
from typing import Optional, Tuple
from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError,
    FloodWaitError,
    PhoneNumberInvalidError,
    PhoneNumberBannedError,
)
from telethon.sessions import StringSession

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config


class SessionCreator:
    """
    Handles Telethon session creation through an interactive flow.
    Manages the complete login process including 2FA.
    """
    
    def __init__(self, user_id: int):
        """Initialize the session creator with API credentials."""
        self.api_id = config.API_ID
        self.api_hash = config.API_HASH
        self.user_id = user_id
        # Each user gets their own session file
        self.session_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sessions",
            f"session_{user_id}"
        )
        # Ensure sessions directory exists
        os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
        
        self.client: Optional[TelegramClient] = None
        self.phone_number: Optional[str] = None
        self.phone_code_hash: Optional[str] = None
        
    async def start_login(self, phone_number: str) -> Tuple[bool, str]:
        """
        Start the login process by sending a verification code.
        
        Args:
            phone_number: User's phone number with country code (e.g., +1234567890)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Clean phone number
            self.phone_number = phone_number.strip().replace(" ", "").replace("-", "")
            
            # Disconnect existing client if any
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
            
            # Delete old session file to start fresh
            self.delete_session()
            
            # Create client with session file
            self.client = TelegramClient(
                self.session_path,
                self.api_id,
                self.api_hash,
                device_model="Desktop",
                system_version="Windows 10",
                app_version="1.0.0",
                lang_code="en",
                connection_retries=5,
                retry_delay=1,
                auto_reconnect=True
            )
            
            await self.client.connect()
            
            # Send verification code
            sent_code = await self.client.send_code_request(self.phone_number)
            self.phone_code_hash = sent_code.phone_code_hash
            
            # Store for later use
            self._sent_code = sent_code
            
            return True, "✅ Tasdiqlash kodi yuborildi! Iltimos, kelgan kodni kiriting."
            
        except PhoneNumberInvalidError:
            return False, "❌ Noto'g'ri telefon formati. Xalqaro formatda kiriting (masalan, +998901234567)."
        except PhoneNumberBannedError:
            return False, "❌ Bu telefon raqami Telegram'da bloklangan."
        except FloodWaitError as e:
            return False, f"❌ Juda ko'p urinish. {e.seconds} soniya kutib qaytadan urinib ko'ring."
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    async def verify_code(self, code: str) -> Tuple[bool, str, bool]:
        """
        Verify the login code sent to the user's phone.
        
        Args:
            code: The verification code received via Telegram
            
        Returns:
            Tuple of (success: bool, message: str, needs_2fa: bool)
        """
        if not self.client or not self.phone_number or not self.phone_code_hash:
            return False, "❌ Sessiya tugadi. /start bilan qaytadan boshlang.", False
            
        try:
            # Clean the code - remove ALL non-digit characters
            code = ''.join(filter(str.isdigit, code))
            
            if not code:
                return False, "❌ Faqat raqamlarni kiriting.", False
            
            # Ensure client is connected
            if not self.client.is_connected():
                await self.client.connect()
            
            # Try to sign in with the code
            await self.client.sign_in(
                phone=self.phone_number,
                code=code,
                phone_code_hash=self.phone_code_hash
            )
            
            # Success - session is created
            return True, "✅ Muvaffaqiyatli kirildi! Sessiya yaratildi.", False
            
        except SessionPasswordNeededError:
            # 2FA is enabled, need password
            return True, "🔐 Ikki bosqichli autentifikatsiya yoqilgan. 2FA parolingizni kiriting.", True
            
        except PhoneCodeInvalidError:
            # Try to resend code automatically
            try:
                sent_code = await self.client.send_code_request(self.phone_number)
                self.phone_code_hash = sent_code.phone_code_hash
                return False, "❌ Noto'g'ri kod. Yangi kod yuborildi! Yangi kodni kiriting.", False
            except Exception:
                return False, "❌ Noto'g'ri kod. Qaytadan urinib ko'ring.", False
            
        except PhoneCodeExpiredError:
            # Try to resend code automatically
            try:
                sent_code = await self.client.send_code_request(self.phone_number)
                self.phone_code_hash = sent_code.phone_code_hash
                return False, "⏰ Kod eskirdi. Yangi kod yuborildi! Yangi kodni kiriting.", False
            except Exception:
                return False, "❌ Kod eskirdi. 'Cancel' bosib qaytadan boshlang.", False
            
        except FloodWaitError as e:
            return False, f"❌ Juda ko'p urinish. {e.seconds} soniya kuting.", False
            
        except Exception as e:
            return False, f"❌ Error: {str(e)}", False
    
    async def verify_2fa(self, password: str) -> Tuple[bool, str]:
        """
        Verify the 2FA password.
        
        Args:
            password: The two-factor authentication password
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.client:
            return False, "❌ Sessiya tugadi. Qaytadan boshlang."
            
        try:
            await self.client.sign_in(password=password)
            return True, "✅ 2FA bilan muvaffaqiyatli kirildi! Sessiya yaratildi."
            
        except PasswordHashInvalidError:
            return False, "❌ Noto'g'ri parol. Qaytadan urinib ko'ring."
            
        except FloodWaitError as e:
            return False, f"❌ Juda ko'p urinish. {e.seconds} soniya kuting."
            
        except Exception as e:
            return False, f"❌ Error: {str(e)}"
    
    async def get_session_string(self) -> Optional[str]:
        """
        Get the session as a string (alternative to file-based session).
        
        Returns:
            Session string or None if not logged in
        """
        if not self.client or not await self.client.is_user_authorized():
            return None
            
        # Create a new client with StringSession to export
        string_session = StringSession.save(self.client.session)
        return string_session
    
    async def get_user_info(self) -> Optional[dict]:
        """
        Get information about the logged-in user.
        
        Returns:
            Dict with user info or None if not logged in
        """
        if not self.client:
            return None
            
        try:
            me = await self.client.get_me()
            return {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name or "",
                "username": me.username or "",
                "phone": me.phone or ""
            }
        except Exception:
            return None
    
    async def disconnect(self):
        """Disconnect the client and cleanup."""
        if self.client:
            # Ensure session is saved before disconnecting
            if self.client.session:
                self.client.session.save()
            await self.client.disconnect()
            self.client = None
        self.phone_number = None
        self.phone_code_hash = None
    
    def session_exists(self) -> bool:
        """Check if a session file already exists."""
        session_file = f"{self.session_path}.session"
        return os.path.exists(session_file)
    
    def delete_session(self) -> bool:
        """Delete the existing session file."""
        session_file = f"{self.session_path}.session"
        try:
            if os.path.exists(session_file):
                os.remove(session_file)
            return True
        except Exception:
            return False


# Global session creator instance for managing state across handlers
session_creators: dict = {}


def get_session_creator(user_id: int) -> SessionCreator:
    """
    Get or create a SessionCreator instance for a specific user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        SessionCreator instance
    """
    if user_id not in session_creators:
        session_creators[user_id] = SessionCreator(user_id)
    return session_creators[user_id]


def get_user_session_path(user_id: int) -> str:
    """Get the session file path for a specific user."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "sessions",
        f"session_{user_id}.session"
    )


def remove_session_creator(user_id: int):
    """
    Remove and cleanup a SessionCreator instance.
    
    Args:
        user_id: Telegram user ID
    """
    if user_id in session_creators:
        del session_creators[user_id]
