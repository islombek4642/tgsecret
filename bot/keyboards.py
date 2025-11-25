"""
Keyboard layouts for the Telegram login bot.
Contains all inline keyboards and reply keyboards used in the bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove


class Keyboards:
    """Collection of keyboard layouts for the bot."""
    
    # Button text constants
    BTN_CANCEL = "❌ Bekor qilish"
    
    @staticmethod
    def start_keyboard() -> InlineKeyboardMarkup:
        """
        Creates the initial start keyboard.
        Shows only the Connect Account button initially.
        """
        keyboard = [
            [InlineKeyboardButton("🔗 Akkaunt ulash", callback_data="connect_account")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def cancel_keyboard() -> InlineKeyboardMarkup:
        """
        Creates a cancel button keyboard.
        Allows user to abort the login process at any point.
        """
        keyboard = [
            [InlineKeyboardButton(Keyboards.BTN_CANCEL, callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def phone_request_keyboard() -> ReplyKeyboardMarkup:
        """
        Creates a keyboard to request phone number.
        Includes both share contact button and manual entry option.
        """
        keyboard = [
            ["📱 Telefon raqamni ulashish"],
            [Keyboards.BTN_CANCEL]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def remove_keyboard() -> ReplyKeyboardRemove:
        """Removes any active reply keyboard."""
        return ReplyKeyboardRemove()
    
    @staticmethod
    def retry_keyboard() -> InlineKeyboardMarkup:
        """
        Creates a retry button keyboard.
        Shown when login fails and user can try again.
        """
        keyboard = [
            [InlineKeyboardButton("🔄 Qaytadan urinish", callback_data="connect_account")],
            [InlineKeyboardButton(Keyboards.BTN_CANCEL, callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def success_keyboard() -> InlineKeyboardMarkup:
        """
        Creates success action keyboard.
        Shown after successful login with option to start userbot.
        """
        keyboard = [
            [InlineKeyboardButton("🚀 Userbotni ishga tushirish", callback_data="start_userbot")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def main_menu_keyboard() -> InlineKeyboardMarkup:
        """
        Creates main menu keyboard with all control options.
        """
        keyboard = [
            [InlineKeyboardButton("🔗 Akkaunt ulash", callback_data="connect_account")],
            [InlineKeyboardButton("🚀 Userbot ishga tushirish", callback_data="start_userbot")],
            [InlineKeyboardButton("⏰ Qayta ishga tushirish", callback_data="wakeup_userbot")],
            [InlineKeyboardButton("📊 Holat", callback_data="check_status")],
            [InlineKeyboardButton("🚪 Chiqish (Logout)", callback_data="logout")]
        ]
        return InlineKeyboardMarkup(keyboard)
