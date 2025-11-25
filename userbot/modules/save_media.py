"""
Save Media Module (.ok command)
Downloads and saves any media (including view-once/disappearing) to Saved Messages.
Only works when replying to a message containing media.
"""

import os
import sys
import asyncio
from datetime import datetime

from telethon import TelegramClient, events
from telethon.tl.types import Message

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config
from userbot.loader import ModuleInfo, command


# Store client reference for handlers
_client: TelegramClient = None


async def save_media_handler(event):
    """
    Handler for .ok command.
    Downloads media from replied message and sends to Saved Messages.
    """
    # Import utils here to avoid circular imports
    from userbot.modules.utils import (
        has_media,
        get_media_type,
        get_filename,
        download_media,
        send_to_saved_messages,
        cleanup_temp_file,
        format_file_size,
        is_view_once,
    )
    
    # Check if this is a reply
    reply = await event.get_reply_message()
    
    if not reply:
        # No reply - silently ignore (stealth mode)
        return
    
    if not has_media(reply):
        # No media in replied message - silently ignore
        return
    
    # Get media info
    media_type = get_media_type(reply)
    is_disappearing = is_view_once(reply)
    
    # Download the media
    filepath = await download_media(_client, reply)
    
    if not filepath:
        # Download failed - silently fail
        return
    
    try:
        # Get file info
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        filename = os.path.basename(filepath)
        
        # Create caption
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'Unknown')
        
        caption_parts = [
            f"📁 **Saqlangan Media**",
            f"",
            f"**Turi:** {media_type}",
            f"**Fayl:** `{filename}`",
            f"**Hajmi:** {format_file_size(file_size)}",
        ]
        
        if is_disappearing:
            caption_parts.append(f"**⏱️ Bir martalik:** Ha")
        
        caption_parts.extend([
            f"",
            f"**Qayerdan:** {chat_title}",
            f"**Saqlangan:** {timestamp}",
        ])
        
        caption = "\n".join(caption_parts)
        
        # Send to Saved Messages
        success = await send_to_saved_messages(_client, filepath, caption)
        
        if not success:
            # Send failed - silently fail
            pass
            
    finally:
        # Clean up temp file
        cleanup_temp_file(filepath)


def setup(client: TelegramClient, loader) -> ModuleInfo:
    """
    Setup function called by the module loader.
    Registers the .ok command handler.
    
    Args:
        client: Telethon client instance
        loader: Module loader instance
        
    Returns:
        ModuleInfo with module details
    """
    global _client
    _client = client
    
    # Get the owner_id for this userbot instance
    owner_id = loader.owner_id
    
    # Create module info
    module_info = ModuleInfo(
        name="Media Saqlash",
        description="Har qanday mediani (bir martalik ham) Saqlangan Xabarlarga saqlaydi",
        commands=["ok"]
    )
    
    # Create the event handler with owner check and auto-delete
    @client.on(events.NewMessage(pattern=f"^\\.ok$", outgoing=True))
    async def ok_handler(event):
        """Handler wrapper with owner verification."""
        # Only respond to this userbot's owner
        if owner_id and event.sender_id != owner_id:
            return
        
        # Don't delete in Saved Messages
        is_saved_messages = event.chat_id == event.sender_id
        
        if not is_saved_messages:
            try:
                # Delete the command message (stealth) - only in other chats
                await event.delete()
            except Exception:
                pass
        
        # Execute the main handler
        await save_media_handler(event)
    
    return module_info
