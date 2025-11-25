"""
Help Module (.help command)
Displays a list of all loaded modules and their commands.
The help message auto-deletes after a configurable delay.
"""

import os
import sys
import asyncio

from telethon import TelegramClient, events
from telethon.tl.types import Message

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config
from userbot.loader import ModuleInfo


# Store references
_client: TelegramClient = None
_loader = None


async def help_handler(event):
    """
    Handler for .help command.
    Shows all loaded modules and their commands.
    """
    if _loader is None:
        return
    
    # Build help message
    help_text_parts = [
        "🤖 **Userbot Yordam**",
        "━" * 20,
        ""
    ]
    
    modules = _loader.get_all_modules()
    
    for name, info in modules.items():
        if info.commands:
            commands_str = " | ".join([f"`.{cmd}`" for cmd in info.commands])
            help_text_parts.append(f"📦 **{info.name}**")
            help_text_parts.append(f"   {info.description}")
            help_text_parts.append(f"   Buyruqlar: {commands_str}")
            help_text_parts.append("")
    
    # Add usage notes
    help_text_parts.extend([
        "━" * 20,
        "📝 **Qisqacha qo'llanma:**",
        "",
        "`.ok` - Mediaga javob berib saqlash",
        "`.ask <savol>` - AI dan savol so'rash",
        "`.ask` (javob) - Xabar haqida so'rash",
        "`.transcribe` - Audio/voice/video ni matnga (javob berib)",
        "`.help` - Ushbu yordam",
    ])
    
    help_text = "\n".join(help_text_parts)
    
    # Send help message to Saved Messages
    await _client.send_message("me", help_text)


def setup(client: TelegramClient, loader) -> ModuleInfo:
    """
    Setup function called by the module loader.
    Registers the .help command handler.
    
    Args:
        client: Telethon client instance
        loader: Module loader instance
        
    Returns:
        ModuleInfo with module details
    """
    global _client, _loader
    _client = client
    _loader = loader
    
    # Get the owner_id for this userbot instance
    owner_id = loader.owner_id
    
    # Create module info
    module_info = ModuleInfo(
        name="Yordam",
        description="Barcha mavjud buyruqlar va modullarni ko'rsatadi",
        commands=["help"]
    )
    
    # Create the event handler
    @client.on(events.NewMessage(pattern=r"^\.help$", outgoing=True))
    async def help_event_handler(event):
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
        await help_handler(event)
    
    return module_info
