# 🤖 TGSecret - Advanced Telegram Userbot System

A powerful multi-user Telegram userbot system with an intuitive bot interface, advanced AI features, and comprehensive session management.

## ✨ Key Features

### 🔐 **Smart Authentication System**
- **Telegram Bot Interface**: Seamless login through Telegram bot
- **Multi-User Support**: Independent userbot instances for each user
- **Advanced Session Management**: Automatic session creation, validation, and cleanup
- **2FA Support**: Full two-factor authentication compatibility
- **Security First**: Owner-only access with session isolation

### 🎙️ **AI-Powered Audio Transcription**
- **Universal Format Support**: MP3, WAV, OGG, FLAC, WebM, M4A, and more
- **Video Processing**: Automatic audio extraction from video files
- **90+ Languages**: Auto-detection with high accuracy
- **Whisper AI Integration**: Powered by OpenAI's Whisper via Groq API
- **Smart Message Handling**: Automatic splitting for long transcriptions
- **Real-time Processing**: Fast transcription with progress updates

### 🤖 **Advanced Userbot Features**
- **AI Chat Assistant**: Intelligent conversations via `.ask` command
- **Comprehensive Help System**: Dynamic command discovery with `.help`
- **Modular Architecture**: Easy plugin system for custom modules
- **Auto-Sleep Management**: Configurable resource optimization
- **Background Processing**: Independent userbot instances

### 🛡️ **Enterprise-Grade Security**
- **Access Control**: Strict owner-only authentication
- **Session Isolation**: Complete user data separation
- **Resource Management**: Automatic cleanup and optimization
- **Error Handling**: Comprehensive exception management
- **Audit Trail**: Detailed logging and monitoring

### 📋 **Admin Panel Features**
- **Channel Management**: Multi-channel subscription enforcement
- **Dynamic Configuration**: Real-time settings updates
- **User Monitoring**: Session status and activity tracking
- **Bulk Operations**: Efficient multi-user management

## 🏗️ Architecture

```
tgsecret/
├── 📁 bot/                    # Telegram Bot Components
│   ├── 🔧 handlers.py         # Message & callback handlers
│   ├── ⌨️ keyboards.py        # Interactive keyboard layouts
│   ├── 🔐 session_creator.py  # Session management logic
│   ├── 🎙️ transcribe_handler.py # Audio transcription system
│   ├── ⚙️ admin_commands.py   # Administrative functions
│   └── 📝 constants.py        # Bot constants and messages
├── 📁 userbot/               # Userbot Core System
│   ├── 🚀 main.py            # Userbot entry point
│   ├── 🔌 loader.py          # Dynamic module loader
│   └── 📁 modules/           # Feature Modules
│       ├── 🤖 ai_chat.py     # AI conversation system
│       ├── ❓ help.py         # Help and documentation
│       └── 🎵 voice_to_text.py # Audio transcription module
├── 📁 sessions/              # User session storage (auto-created)
├── 🔧 main.py               # Application entry point
├── ⚙️ config.py             # Configuration management
├── 📋 requirements.txt      # Python dependencies
└── 📖 README.md             # This documentation
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (Recommended: Python 3.11+)
- **Telegram Bot Token** (Get from [@BotFather](https://t.me/BotFather))
- **Telegram API Credentials** (Get from [my.telegram.org](https://my.telegram.org))
- **Groq API Key** (Optional, get from [groq.com](https://groq.com))

### Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/islombek4642/tgsecret.git
   cd tgsecret
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   Create `.env` file:
   ```env
   # Required Settings
   BOT_TOKEN=your_bot_token_from_botfather
   API_ID=your_api_id_from_my_telegram_org
   API_HASH=your_api_hash_from_my_telegram_org
   OWNER_ID=your_telegram_user_id
   
   # Optional Settings
   GROQ_API_KEY=your_groq_api_key_for_ai_features
   AUTO_SLEEP_HOURS=12
   REQUIRED_CHANNEL=@channel1,@channel2  # Comma-separated
   ```

4. **Launch System**
   ```bash
   python main.py
   ```

## 📱 Usage Guide

### Initial Setup
1. **Start the System**: Run `python main.py`
2. **Open Telegram**: Message your bot
3. **Access Control Panel**: Send `/start` command
4. **Connect Account**: Click "🔗 Akkaunt ulash"
5. **Authentication**: Enter phone number and verification code
6. **Activate Userbot**: Click "🚀 Ishga tushirish"

### Bot Commands
| Command | Description |
|---------|-------------|
| `/start` | Main control panel |
| `/admin` | Admin panel (owner only) |
| `/transcribe` | Audio transcription info |

### Userbot Commands
| Command | Function | Example |
|---------|----------|---------|
| `.ask <question>` | AI conversation | `.ask What is Python?` |
| `.transcribe` | Audio transcription | Reply to voice message |
| `.help` | Command list | `.help` |

### Control Panel
- **🔗 Akkaunt ulash**: Connect Telegram account
- **🚀 Ishga tushirish**: Start userbot instance
- **⏰ Qayta ishga tushirish**: Restart userbot
- **📊 Holat**: Check system status
- **🚪 Chiqish**: Logout and cleanup

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `BOT_TOKEN` | ✅ | Telegram bot token | `123456:ABC-DEF...` |
| `API_ID` | ✅ | Telegram API ID | `1234567` |
| `API_HASH` | ✅ | Telegram API hash | `abcdef123456...` |
| `OWNER_ID` | ✅ | Your Telegram user ID | `987654321` |
| `GROQ_API_KEY` | ❌ | Groq API for AI features | `gsk_...` |
| `AUTO_SLEEP_HOURS` | ❌ | Auto-sleep timer (0=disabled) | `12` |
| `REQUIRED_CHANNEL` | ❌ | Mandatory subscription channels | `@chan1,@chan2` |

### Getting Credentials

#### 🤖 Bot Token
1. Message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow instructions
4. Copy the token

#### 🔑 API Credentials
1. Visit [my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Go to "API development tools"
4. Create new application
5. Copy `api_id` and `api_hash`

#### 👤 User ID
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your user ID

#### 🧠 Groq API Key
1. Visit [groq.com](https://groq.com)
2. Sign up for free account
3. Go to API keys section
4. Create new key

## 🔧 Muammolarni Hal Qilish

### "Sessiya topilmadi"
- Bot orqali akkauntni ulashni yakunlang

### "Sessiya avtorizatsiya qilinmagan"
- Sessiyangiz muddati o'tgan yoki bekor qilingan
- `sessions/` papkasidagi faylni o'chiring va qayta ulaning

### "Noto'g'ri API ma'lumotlari"
- `.env` fayldagi `API_ID` va `API_HASH` ni tekshiring
- Ortiqcha bo'shliqlar yoki qo'shtirnoqlar yo'qligiga ishonch hosil qiling

### "Modul yuklanmadi"
- Modul faylida sintaksis xatolarini tekshiring
- Barcha importlar to'g'ri ekanligiga ishonch hosil qiling

### AI javob bermayapti
- `GROQ_API_KEY` to'g'ri ekanligini tekshiring
- Groq akkauntingizda API kreditlari borligini tekshiring

### "database is locked"
- Bir nechta userbot bitta sessiyadan foydalanmoqda
- Botni qayta ishga tushiring

## ⚙️ Konfiguratsiya

| O'zgaruvchi | Tavsif | Majburiy |
|-------------|--------|----------|
| `BOT_TOKEN` | Telegram bot tokeni | Ha |
| `API_ID` | Telegram API ID | Ha |
| `API_HASH` | Telegram API Hash | Ha |
| `OWNER_ID` | Sizning Telegram ID | Ha |
| `GROQ_API_KEY` | Groq AI API kaliti | Yo'q |
| `REQUIRED_CHANNEL` | Majburiy obuna kanali (@username) | Yo'q |
| `AUTO_SLEEP_HOURS` | Avtomatik uxlash vaqti (soat) | Yo'q (standart: 24) |

## 📄 Litsenziya

Bu loyiha ta'lim maqsadlarida yaratilgan. Telegram Xizmat shartlariga muvofiq foydalaning.

## ⚠️ Ogohlantirish

- Bu userbot faqat shaxsiy foydalanish uchun mo'ljallangan
- Spam, bezovtalik yoki zararli maqsadlarda foydalanmang
- Ishlab chiquvchilar noto'g'ri foydalanish uchun javobgar emas
- Userbotlardan foydalanish Telegram shartlarini buzishi mumkin - o'z xavfingiz bilan foydalaning

## 🤝 Yordam

Muammolarga duch kelsangiz:
1. Yuqoridagi "Muammolarni Hal Qilish" bo'limini tekshiring
2. Barcha kutubxonalar to'g'ri o'rnatilganligiga ishonch hosil qiling
3. `.env` konfiguratsiyasini tekshiring
4. Python versiyasi mosligini tekshiring (3.9+)
