"""
Admin Commands for Bot Owner
Only accessible by OWNER_ID
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import config

# Constants for repeated strings
TELEGRAM_URL = "t.me/"
NOT_SET_TEXT = "❌ O'rnatilmagan"
BACK_BUTTON_TEXT = "◀️ Orqaga"
ACCESS_DENIED_TEXT = "❌ Ruxsat yo'q!"
REQUIRED_CHANNEL_KEY = "REQUIRED_CHANNEL="

# Async file helper
import aiofiles

async def read_env_file(file_path: str) -> list:
    """Read .env file asynchronously"""
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return content.splitlines(keepends=True)
    except FileNotFoundError:
        return []

async def write_env_file(file_path: str, lines: list):
    """Write .env file asynchronously"""
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
        await f.writelines(lines)


def parse_channel_id(text: str) -> str:
    """Parse channel ID from text (link, username, or ID) and normalize it"""
    text = text.strip()
    
    if TELEGRAM_URL in text:
        # Extract from link
        if "/c/" in text:
            # Private channel: https://t.me/c/1234567890/123
            parts = text.split("/c/")[1].split("/")[0]
            return f"-100{parts}"
        else:
            # Public channel: https://t.me/username
            username = text.split(TELEGRAM_URL)[1].split("/")[0].split("?")[0]
            # Normalize: always use @ format for usernames
            return f"@{username}" if not username.startswith("@") else username
    else:
        # Direct input - could be @username or ID
        if not text.startswith("-") and not text.startswith("@"):
            # Just username without @
            return f"@{text}"
        return text


def get_admin_keyboard():
    """Get admin panel keyboard"""
    channels = config.get_required_channels()
    channel_count = len(channels)
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Bot Sozlamalari", callback_data="admin_config")],
        [InlineKeyboardButton(f"📋 Kanallar ({channel_count})", callback_data="admin_channels_view")],
        [InlineKeyboardButton("➕ Kanal Qo'shish", callback_data="admin_add_channel_info")],
        [InlineKeyboardButton("🗑 Kanal O'chirish", callback_data="admin_remove_channel_info")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="admin_refresh")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def cmd_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel (OWNER only)"""
    user_id = update.effective_user.id
    
    # Check if user is owner
    if user_id != config.OWNER_ID:
        return  # Silently ignore non-owners
    
    # Force reload to get latest channels
    config.reload_channels()
    channels = config.get_required_channels()
    channel_count = len(channels)
    
    if channel_count == 0:
        status_text = NOT_SET_TEXT
    elif channel_count == 1:
        status_text = f"✅ 1 ta kanal: `{channels[0]}`"
    else:
        status_text = f"✅ {channel_count} ta kanal o'rnatilgan"
    
    admin_text = (
        "🔧 **Admin Panel**\n\n"
        f"**Holat:** {status_text}\n\n"
        "Kerakli amalni tanlang:"
    )
    
    await update.message.reply_text(
        admin_text,
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )


async def handle_admin_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot configuration"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        return
    
    required_channel = config.REQUIRED_CHANNEL or NOT_SET_TEXT
    owner_id = config.OWNER_ID
    auto_sleep = config.AUTO_SLEEP_HOURS
    groq_configured = "✅ Ha" if config.GROQ_API_KEY else "❌ Yo'q"
    
    config_text = (
        "⚙️ **Bot Sozlamalari**\n\n"
        f"**Owner ID:** `{owner_id}`\n"
        f"**Majburiy kanal:** `{required_channel}`\n"
        f"**Auto Sleep:** {auto_sleep} soat\n"
        f"**Groq AI:** {groq_configured}\n\n"
        "Asosiy menyuga qaytish uchun tugmani bosing."
    )
    
    keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")]]
    
    await query.edit_message_text(
        config_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show instructions for setting channel"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        return
    
    current = config.REQUIRED_CHANNEL or "O'rnatilmagan"
    
    help_text = (
        "📢 **Majburiy Obuna Kanal Sozlash**\n\n"
        f"**Hozirgi kanal:** `{current}`\n\n"
        "**Qanday o'rnatish:**\n"
        "Kanal ID, username yoki link bilan:\n\n"
        "`/setchannel -1001234567890`\n"
        "`/setchannel @kanalUsername`\n"
        "`/setchannel https://t.me/kanalUsername`\n\n"
        "**⚠️ Muhim:** Botni kanalga admin qilib qo'shing!"
    )
    
    keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")]]
    
    await query.edit_message_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove required channel via callback"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id != config.OWNER_ID:
        await query.answer(ACCESS_DENIED_TEXT)
        return
    
    # Check if channel is set
    if not config.REQUIRED_CHANNEL:
        await query.answer("⚠️ Kanal o'rnatilmagan!", show_alert=True)
        return
    
    # Update .env file
    env_path = ".env"
    try:
        # Read current .env
        lines = await read_env_file(env_path)
        
        # Remove REQUIRED_CHANNEL line
        new_lines = [line for line in lines if not line.startswith(REQUIRED_CHANNEL_KEY)]
        
        # Write back
        await write_env_file(env_path, new_lines)
        
        # Update config in memory
        old_channel = config.REQUIRED_CHANNEL
        config.REQUIRED_CHANNEL = None
        
        await query.answer(f"✅ Kanal o'chirildi: {old_channel}")
        
        # Show updated admin panel
        admin_text = (
            "🔧 **Admin Panel**\n\n"
            "**Hozirgi kanal:** `❌ O'rnatilmagan`\n\n"
            "Kerakli amalni tanlang:"
        )
        
        await query.edit_message_text(
            admin_text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await query.answer(f"❌ Xatolik: {str(e)}", show_alert=True)


async def handle_admin_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Refresh admin panel"""
    query = update.callback_query
    
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        await query.answer(ACCESS_DENIED_TEXT)
        return
    
    required_channel = config.REQUIRED_CHANNEL or NOT_SET_TEXT
    
    admin_text = (
        "🔧 **Admin Panel**\n\n"
        f"**Hozirgi kanal:** `{required_channel}`\n\n"
        "Kerakli amalni tanlang:"
    )
    
    try:
        await query.edit_message_text(
            admin_text,
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
        await query.answer("🔄 Yangilandi!")
    except Exception:
        # Message not modified - content is same
        await query.answer("✅ Allaqachon yangilangan!")


async def cmd_set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set required channel for subscription (OWNER only)"""
    user_id = update.effective_user.id
    
    # Check if user is owner
    if user_id != config.OWNER_ID:
        return  # Silently ignore non-owners
    
    # Check if channel ID/username is provided
    if not context.args:
        current = config.REQUIRED_CHANNEL or "O'rnatilmagan"
        await update.message.reply_text(
            f"📢 **Majburiy obuna sozlamalari**\n\n"
            f"**Hozirgi kanal:** `{current}`\n\n"
            f"**Qanday ishlatish:**\n"
            f"• Kanal ID: `/setchannel -1001234567890`\n"
            f"• Username: `/setchannel @kanalUsername`\n"
            f"• Link: `/setchannel https://t.me/kanalUsername`\n"
            f"• O'chirish: `/removechannel`\n\n"
            f"**Eslatma:** Bot kanalda admin bo'lishi kerak!",
            parse_mode="Markdown"
        )
        return
    
    channel_input = context.args[0]
    
    # Parse channel link if provided
    channel_id = channel_input
    if "t.me/" in channel_input:
        # Extract from link: https://t.me/username or https://t.me/c/1234567890/...
        if "/c/" in channel_input:
            # Private channel: https://t.me/c/1234567890/123
            parts = channel_input.split("/c/")[1].split("/")[0]
            channel_id = f"-100{parts}"
        else:
            # Public channel: https://t.me/username
            username = channel_input.split(TELEGRAM_URL)[1].split("/")[0].split("?")[0]
            channel_id = f"@{username}" if not username.startswith("@") else username
    
    # Update .env file
    env_path = ".env"
    try:
        # Read current .env
        lines = await read_env_file(env_path)
        
        # Update or add REQUIRED_CHANNEL
        found = False
        for i, line in enumerate(lines):
            if line.startswith(REQUIRED_CHANNEL_KEY):
                lines[i] = f'REQUIRED_CHANNEL={channel_id}\n'
                found = True
                break
        
        if not found:
            lines.append(f'\nREQUIRED_CHANNEL={channel_id}\n')
        
        # Write back
        await write_env_file(env_path, lines)
        
        # Update config in memory
        config.REQUIRED_CHANNEL = channel_id
        
        await update.message.reply_text(
            f"✅ **Majburiy obuna o'rnatildi!**\n\n"
            f"**Kanal:** `{channel_id}`\n\n"
            f"Endi barcha foydalanuvchilar bu kanalga obuna bo'lishi kerak.\n\n"
            f"⚠️ **Muhim:** Botni kanalga admin qilib qo'shishni unutmang!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **Xatolik!**\n\n"
            f"Sozlamalarni yangilashda muammo: {str(e)}",
            parse_mode="Markdown"
        )


async def cmd_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove required channel (OWNER only)"""
    user_id = update.effective_user.id
    
    # Check if user is owner
    if user_id != config.OWNER_ID:
        return  # Silently ignore non-owners
    
    # Update .env file
    env_path = ".env"
    try:
        # Read current .env
        lines = await read_env_file(env_path)
        
        # Remove REQUIRED_CHANNEL line
        new_lines = [line for line in lines if not line.startswith(REQUIRED_CHANNEL_KEY)]
        
        # Write back
        await write_env_file(env_path, new_lines)
        
        # Update config in memory
        config.REQUIRED_CHANNEL = None
        
        await update.message.reply_text(
            "✅ **Majburiy obuna o'chirildi!**\n\n"
            "Endi barcha foydalanuvchilar botdan erkin foydalanishlari mumkin.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **Xatolik!**\n\n"
            f"Sozlamalarni yangilashda muammo: {str(e)}",
            parse_mode="Markdown"
        )


async def cmd_check_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check current bot configuration (OWNER only)"""
    user_id = update.effective_user.id
    
    # Check if user is owner
    if user_id != config.OWNER_ID:
        return  # Silently ignore non-owners
    
    required_channel = config.REQUIRED_CHANNEL or NOT_SET_TEXT
    owner_id = config.OWNER_ID
    auto_sleep = config.AUTO_SLEEP_HOURS
    groq_configured = "✅ Ha" if config.GROQ_API_KEY else "❌ Yo'q"
    
    config_text = (
        "⚙️ **Bot Sozlamalari**\n\n"
        f"**Owner ID:** `{owner_id}`\n"
        f"**Majburiy kanal:** `{required_channel}`\n"
        f"**Auto Sleep:** {auto_sleep} soat\n"
        f"**Groq AI:** {groq_configured}\n\n"
        "**Admin buyruqlar:**\n"
        "• `/setchannel <ID/username>` - Kanal sozlash\n"
        "• `/removechannel` - Kanalni o'chirish\n"
        "• `/config` - Sozlamalarni ko'rish"
    )
    
    await update.message.reply_text(config_text, parse_mode="Markdown")


async def handle_admin_channels_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show view-only list of channels with pagination (10 per page)"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        return
    
    # Extract page number
    callback_data = query.data
    page = int(callback_data.split("_")[-1]) if "_" in callback_data and callback_data.split("_")[-1].isdigit() else 0
    
    # Force reload from .env to get latest channels
    config.reload_channels()
    channels = config.get_required_channels()
    
    if not channels:
        text = "📋 **Kanallar Ro'yxati**\n\n❌ Hech qanday kanal o'rnatilmagan.\n\n➕ Kanal qo'shish uchun admin paneldan."
        keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")]]
    else:
        # Pagination: 10 channels per page
        per_page = 10
        total_pages = (len(channels) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(channels))
        
        text = f"📋 **Kanallar Ro'yxati** ({len(channels)} ta)\n"
        text += f"📄 Sahifa {page + 1}/{total_pages}\n\n"
        
        for i in range(start_idx, end_idx):
            channel = channels[i]
            text += f"{i + 1}. `{channel}`\n"
        
        # Pagination buttons
        keyboard = []
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_channels_view_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ Keyingi", callback_data=f"admin_channels_view_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_channels_manage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channels management with delete buttons (10 per page)"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        return
    
    # Extract page number
    callback_data = query.data
    page = int(callback_data.split("_")[-1])
    
    channels = config.get_required_channels()
    
    if not channels:
        text = "🗑 **Kanallarni Boshqarish**\n\n❌ Hech qanday kanal o'rnatilmagan."
        keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")]]
    else:
        # Pagination: 10 channels per page
        per_page = 10
        total_pages = (len(channels) + per_page - 1) // per_page
        start_idx = page * per_page
        end_idx = min(start_idx + per_page, len(channels))
        
        text = f"🗑 **Kanallarni Boshqarish** ({len(channels)} ta)\n"
        text += f"📄 Sahifa {page + 1}/{total_pages}\n\n"
        text += "⚠️ O'chirish uchun kanal tugmasini bosing:\n\n"
        
        keyboard = []
        
        for i in range(start_idx, end_idx):
            channel = channels[i]
            text += f"{i + 1}. `{channel}`\n"
            # Add delete button for each channel
            keyboard.append([
                InlineKeyboardButton(f"🗑 {channel[:25]}..." if len(channel) > 25 else f"🗑 {channel}", 
                                   callback_data=f"remove_channel_{i}")
            ])
        
        # Pagination buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_channels_manage_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("➡️ Keyingi", callback_data=f"admin_channels_manage_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_add_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show info on how to add a channel"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        return
    
    text = (
        "➕ **Kanal Qo'shish**\n\n"
        "Kanal qo'shish uchun shunchaki menga kanal ID, username yoki linkini yuboring:\n\n"
        "**Misol:**\n"
        "• `-1001234567890`\n"
        "• `@myChannel`\n"
        "• `https://t.me/myChannel`\n\n"
        "**⚠️ Muhim:**\n"
        "• Botni kanalga admin qilib qo'shing!\n"
        "• Bir nechta kanal qo'shishingiz mumkin\n"
        "• Foydalanuvchilar **barcha** kanallarga obuna bo'lishi kerak"
    )
    
    keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_admin_remove_channel_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show info on how to remove a channel"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != config.OWNER_ID:
        return
    
    channels = config.get_required_channels()
    
    if not channels:
        text = "🗑 **Kanal O'chirish**\n\n❌ Hech qanday kanal o'rnatilmagan."
        keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")]]
    else:
        text = (
            "🗑 **Kanal O'chirish**\n\n"
            "Kanal o'chirish uchun menga kanal ID, username yoki linkini yuboring:\n\n"
            "**Misol:**\n"
            "• `-1001234567890`\n"
            "• `@myChannel`\n"
            "• `https://t.me/myChannel`\n\n"
            f"**Hozirgi kanallar:** {len(channels)} ta\n\n"
            "📋 Kanallar ro'yxatini ko'rish uchun admin paneldan \"📋 Kanallar\" tugmasini bosing."
        )
        keyboard = [[InlineKeyboardButton(BACK_BUTTON_TEXT, callback_data="admin_refresh")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_channel_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a channel from the list"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    if user_id != config.OWNER_ID:
        await query.answer(ACCESS_DENIED_TEXT)
        return
    
    # Extract channel index from callback data
    callback_data = query.data
    channel_index = int(callback_data.split("_")[-1])
    
    channels = config.get_required_channels()
    
    if channel_index >= len(channels):
        await query.answer("❌ Kanal topilmadi!", show_alert=True)
        return
    
    removed_channel = channels[channel_index]
    channels.pop(channel_index)
    
    # Update .env file
    env_path = ".env"
    try:
        # Read current .env
        lines = await read_env_file(env_path)
        
        # Update or remove REQUIRED_CHANNEL
        new_lines = [line for line in lines if not line.startswith(REQUIRED_CHANNEL_KEY)]
        
        if channels:
            new_lines.append(f'\nREQUIRED_CHANNEL={",".join(channels)}\n')
        
        # Write back
        await write_env_file(env_path, new_lines)
        
        # Update config in memory
        config.REQUIRED_CHANNEL = ",".join(channels) if channels else ""
        
        await query.answer(f"✅ O'chirildi: {removed_channel}")
        
        # Return to manage page (page 0)
        await handle_admin_channels_manage(update, context)
        
    except Exception as e:
        await query.answer(f"❌ Xatolik: {str(e)}", show_alert=True)


async def handle_add_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from OWNER to add or remove channels"""
    user_id = update.effective_user.id
    
    # Only for OWNER
    if user_id != config.OWNER_ID:
        return
    
    text = update.message.text.strip()
    
    # Ignore commands (both bot and userbot)
    if text.startswith('/') or text.startswith('.'):
        return
    
    # Only accept valid channel formats (@username or t.me/username or -100xxx)
    if not (text.startswith('@') or 't.me/' in text or text.startswith('-100') or text.lstrip('-').isdigit()):
        return
    
    # Parse and normalize channel ID
    channel_id = parse_channel_id(text)
    
    # Get current channels
    channels = config.get_required_channels()
    
    # Check if exists - if yes, remove it; if no, add it
    is_removing = channel_id in channels
    
    if is_removing:
        # Remove channel
        channels.remove(channel_id)
    else:
        # Add new channel
        channels.append(channel_id)
    
    # Update .env file
    env_path = ".env"
    try:
        # Read current .env
        lines = await read_env_file(env_path)
        
        # Update or remove REQUIRED_CHANNEL
        new_lines = [line for line in lines if not line.startswith(REQUIRED_CHANNEL_KEY)]
        
        if channels:
            new_lines.append(f'\nREQUIRED_CHANNEL={",".join(channels)}\n')
        
        # Write back
        await write_env_file(env_path, new_lines)
        
        # Update config in memory
        config.REQUIRED_CHANNEL = ",".join(channels) if channels else ""
        
        keyboard = [[InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_refresh")]]
        
        if is_removing:
            await update.message.reply_text(
                f"✅ **Kanal o'chirildi!**\n\n"
                f"**Kanal:** `{channel_id}`\n"
                f"**Qolgan kanallar:** {len(channels)}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✅ **Kanal qo'shildi!**\n\n"
                f"**Kanal:** `{channel_id}`\n"
                f"**Jami kanallar:** {len(channels)}\n\n"
                f"⚠️ **Muhim:** Botni kanalga admin qilib qo'shing!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **Xatolik!**\n\n"
            f"Sozlamalarni yangilashda muammo: {str(e)}",
            parse_mode="Markdown"
        )
