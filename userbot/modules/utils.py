"""
Utility module providing shared helper functions for other modules.
Contains common operations like message handling, formatting, and file operations.
"""

import os
import sys
import asyncio
import tempfile
from typing import Optional, Union, Tuple
from datetime import datetime

from telethon import TelegramClient
from telethon.tl.types import (
    Message,
    MessageMediaPhoto,
    MessageMediaDocument,
    MessageMediaWebPage,
    Document,
    Photo,
    DocumentAttributeFilename,
    DocumentAttributeVideo,
    DocumentAttributeAudio,
    DocumentAttributeAnimated,
    DocumentAttributeSticker,
)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config


# Temporary directory for downloaded files
TEMP_DIR = os.path.join(tempfile.gettempdir(), "userbot_media")


def ensure_temp_dir():
    """Ensure the temporary directory exists."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)


def get_temp_path(filename: str) -> str:
    """
    Get a path in the temporary directory.
    
    Args:
        filename: Name of the file
        
    Returns:
        Full path to the file in temp directory
    """
    ensure_temp_dir()
    return os.path.join(TEMP_DIR, filename)


def cleanup_temp_file(filepath: str) -> bool:
    """
    Delete a temporary file.
    
    Args:
        filepath: Path to the file to delete
        
    Returns:
        True if deleted successfully
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        return True
    except Exception:
        return False


def is_owner(user_id: int) -> bool:
    """
    Check if a user ID belongs to the owner.
    
    Args:
        user_id: Telegram user ID to check
        
    Returns:
        True if user is the owner
    """
    return user_id == config.OWNER_ID


def get_media_type(message: Message) -> Optional[str]:
    """
    Determine the type of media in a message.
    
    Args:
        message: Telegram message object
        
    Returns:
        String describing media type, or None if no media
    """
    if not message or not message.media:
        return None
    
    media = message.media
    
    if isinstance(media, MessageMediaPhoto):
        return "photo"
    
    if isinstance(media, MessageMediaDocument):
        doc = media.document
        if doc:
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeAnimated):
                    return "animation"
                if isinstance(attr, DocumentAttributeSticker):
                    return "sticker"
                if isinstance(attr, DocumentAttributeVideo):
                    if attr.round_message:
                        return "video_note"
                    return "video"
                if isinstance(attr, DocumentAttributeAudio):
                    if attr.voice:
                        return "voice"
                    return "audio"
            return "document"
    
    return "unknown"


def get_filename(message: Message) -> str:
    """
    Extract filename from a message's media.
    
    Args:
        message: Telegram message with media
        
    Returns:
        Filename string
    """
    if not message or not message.media:
        return "unknown"
    
    media = message.media
    
    # Photo
    if isinstance(media, MessageMediaPhoto):
        return f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    # Document
    if isinstance(media, MessageMediaDocument):
        doc = media.document
        if doc:
            # Try to get filename from attributes
            for attr in doc.attributes:
                if isinstance(attr, DocumentAttributeFilename):
                    return attr.file_name
            
            # Generate filename based on mime type
            mime = doc.mime_type or "application/octet-stream"
            ext = mime.split("/")[-1]
            if ext == "octet-stream":
                ext = "bin"
            return f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    
    return f"media_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def has_media(message: Message) -> bool:
    """
    Check if a message contains downloadable media.
    
    Args:
        message: Telegram message to check
        
    Returns:
        True if message has media
    """
    if not message:
        return False
    
    return message.media is not None and not isinstance(message.media, MessageMediaWebPage)


def is_view_once(message: Message) -> bool:
    """
    Check if a message is a view-once (disappearing) media message.
    
    Args:
        message: Telegram message to check
        
    Returns:
        True if message is view-once media
    """
    if not message or not message.media:
        return False
    
    # Check for TTL media
    if hasattr(message.media, 'ttl_seconds') and message.media.ttl_seconds:
        return True
    
    return False


async def download_media(client: TelegramClient, message: Message) -> Optional[str]:
    """
    Download media from a message to temp directory.
    
    Args:
        client: Telethon client
        message: Message containing media
        
    Returns:
        Path to downloaded file, or None if failed
    """
    if not has_media(message):
        return None
    
    try:
        filename = get_filename(message)
        filepath = get_temp_path(filename)
        
        # Download the media
        downloaded = await client.download_media(message, file=filepath)
        
        return downloaded
    except Exception as e:
        print(f"Download error: {e}")
        return None


async def send_to_saved_messages(client: TelegramClient, filepath: str, caption: str = "") -> bool:
    """
    Send a file to the user's Saved Messages.
    
    Args:
        client: Telethon client
        filepath: Path to the file to send
        caption: Optional caption for the file
        
    Returns:
        True if sent successfully
    """
    try:
        # Send to "me" which is Saved Messages
        await client.send_file(
            "me",
            filepath,
            caption=caption,
            force_document=False  # Let Telethon detect the type
        )
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False


async def delete_message_safe(message: Message) -> bool:
    """
    Safely delete a message, ignoring errors.
    
    Args:
        message: Message to delete
        
    Returns:
        True if deleted successfully
    """
    try:
        await message.delete()
        return True
    except Exception:
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def truncate_text(text: str, max_length: int = 4096) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (default 4096 for Telegram)
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


# Module setup (required for loader)
def setup(client: TelegramClient, loader) -> None:
    """
    Setup function called by the module loader.
    Utils module doesn't register any commands, just provides helpers.
    """
    from userbot.loader import ModuleInfo
    
    return ModuleInfo(
        name="utils",
        description="Utility functions for other modules",
        commands=[]
    )
