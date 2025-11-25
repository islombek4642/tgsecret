"""
AI Chat Module (.ask command)
Integrates with Groq API for AI-powered responses using Llama 3 70B.
Supports context from replied messages.
"""

import os
import sys
import asyncio
import aiohttp
from typing import Optional

from telethon import TelegramClient, events
from telethon.tl.types import Message

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import config
from userbot.loader import ModuleInfo


# Store client reference
_client: TelegramClient = None


async def query_groq(prompt: str, context: Optional[str] = None) -> str:
    """
    Send a query to the Groq API.
    
    Args:
        prompt: The user's question/prompt
        context: Optional context from replied message
        
    Returns:
        AI response text
    """
    if not config.GROQ_API_KEY:
        return "❌ Groq API kaliti sozlanmagan. .env fayliga GROQ_API_KEY qo'shing."
    
    # Build messages array
    messages = []
    
    # System message for behavior
    messages.append({
        "role": "system",
        "content": (
            "You are a helpful AI assistant. Provide clear, concise, and accurate responses. "
            "If given context from a previous message, use it to inform your answer. "
            "Keep responses focused and avoid unnecessary verbosity."
        )
    })
    
    # Add context if provided
    if context:
        messages.append({
            "role": "user",
            "content": f"Context from previous message:\n\n{context}"
        })
        messages.append({
            "role": "assistant",
            "content": "I've noted the context. What would you like to know about it?"
        })
    
    # Add the actual prompt
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Prepare request
    headers = {
        "Authorization": f"Bearer {config.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": config.GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "top_p": 0.9,
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.GROQ_API_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                elif response.status == 401:
                    return "❌ Groq API kaliti noto'g'ri. Sozlamalarni tekshiring."
                elif response.status == 429:
                    return "❌ So'rovlar limiti oshdi. Keyinroq urinib ko'ring."
                else:
                    error_text = await response.text()
                    return f"❌ API xatosi ({response.status}): {error_text[:200]}"
                    
    except asyncio.TimeoutError:
        return "❌ So'rov vaqti tugadi. Qaytadan urinib ko'ring."
    except aiohttp.ClientError as e:
        return f"❌ Ulanish xatosi: {str(e)}"
    except Exception as e:
        return f"❌ Kutilmagan xato: {str(e)}"


async def ask_handler(event):
    """
    Handler for .ask command.
    Queries Groq AI and sends response to the same chat.
    """
    from userbot.modules.utils import truncate_text
    
    # Extract the prompt from the command
    message_text = event.raw_text
    
    # Remove the .ask prefix
    prompt = message_text[4:].strip()  # Remove ".ask"
    
    # Get context from replied message if any
    context = None
    reply = await event.get_reply_message()
    
    if reply and reply.text:
        context = reply.text
    
    # If no prompt provided
    if not prompt and not context:
        # Send hint to the same chat
        await event.respond(
            "💡 **Foydalanish:** `.ask <savolingiz>`\n"
            "Yoki xabarga javob berib `.ask` yozing."
        )
        return
    
    # If only context, use a default prompt
    if not prompt and context:
        prompt = "Quyidagi xabarni tushuntiring yoki qisqacha bayonini bering."
    
    # Send "thinking" message
    thinking_msg = await event.respond("🤔 AI o'ylayapti...")
    
    # Query the AI
    response = await query_groq(prompt, context)
    
    # Delete thinking message
    try:
        await thinking_msg.delete()
    except Exception:
        pass  # Ignore delete errors
    
    # Truncate if too long
    response = truncate_text(response, 4000)
    
    # Format the response
    output_parts = ["🤖 **AI Javobi**", ""]
    
    if context:
        # Include truncated context
        context_preview = context[:200] + "..." if len(context) > 200 else context
        output_parts.extend([
            "**Kontekst:**",
            f"```{context_preview}```",
            ""
        ])
    
    output_parts.extend([
        "**Savol:**",
        f"{prompt}",
        "",
        "**Javob:**",
        response
    ])
    
    output = "\n".join(output_parts)
    
    # Send response to the same chat where command was used
    await event.respond(output)


def setup(client: TelegramClient, loader) -> ModuleInfo:
    """
    Setup function called by the module loader.
    Registers the .ask command handler.
    
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
        name="AI Suhbat",
        description="Groq AI bilan aqlli javoblar (istalgan chatda)",
        commands=["ask"]
    )
    
    # Check if Groq is configured
    if not config.validate_groq():
        print("   ⚠️ AI Suhbat: GROQ_API_KEY sozlanmagan")
    
    # Create the event handler
    @client.on(events.NewMessage(pattern=r"^\.ask(\s|$)", outgoing=True))
    async def ask_event_handler(event):
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
        await ask_handler(event)
    
    return module_info
