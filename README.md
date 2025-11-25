# 🤖 TGSecret - Ilg'or Telegram Userbot Tizimi

Ko'p foydalanuvchili Telegram userbot tizimi. Qulay bot interfeysi, AI xususiyatlari va keng qamrovli sessiya boshqaruvi bilan.

## ✨ Asosiy Xususiyatlar

### 🔐 **Aqlli Autentifikatsiya Tizimi**
- **Telegram Bot Interfeysi**: Bot orqali oson kirish
- **Ko'p Foydalanuvchi**: Har bir foydalanuvchi uchun alohida userbot
- **Ilg'or Sessiya Boshqaruvi**: Avtomatik yaratish, tekshirish va tozalash
- **2FA Qo'llab-quvvatlash**: To'liq ikki bosqichli autentifikatsiya
- **Xavfsizlik**: Faqat egasi kirishi mumkin, sessiyalar ajratilgan

### 🎙️ **AI Bilan Audio Transkript**
- **Universal Format**: MP3, WAV, OGG, FLAC, WebM, M4A va boshqalar
- **Video Ishlov Berish**: Video fayllardan audio ajratish
- **90+ Til**: Avtomatik aniqlash, yuqori aniqlik
- **Whisper AI**: OpenAI Whisper via Groq API
- **Aqlli Xabar Boshqaruvi**: Uzun matnlarni avtomatik bo'lish
- **Real-vaqt Ishlov Berish**: Tez transkript, jarayon yangilanishi

### 🤖 **Ilg'or Userbot Xususiyatlari**
- **AI Chat Yordamchisi**: `.ask` buyrug'i orqali aqlli suhbat
- **To'liq Yordam Tizimi**: `.help` bilan dinamik buyruq kashfiyoti
- **Modulli Arxitektura**: Oson plugin tizimi
- **Avtomatik Uyqu**: Sozlanadigan resurs optimallashtirish
- **Fon Ishlov Berish**: Mustaqil userbot nusxalari

### 🛡️ **Korxona Darajasidagi Xavfsizlik**
- **Kirish Nazorati**: Qat'iy faqat egasi autentifikatsiyasi
- **Sessiya Ajratish**: To'liq foydalanuvchi ma'lumotlari ajratish
- **Resurs Boshqaruvi**: Avtomatik tozalash va optimallashtirish
- **Xato Boshqaruvi**: Keng qamrovli istisno boshqaruvi
- **Audit Trail**: Batafsil jurnal va monitoring

### 📋 **Admin Panel Xususiyatlari**
- **Kanal Boshqaruvi**: Ko'p kanalli obuna majburlash
- **Dinamik Konfiguratsiya**: Real-vaqt sozlamalar yangilanishi
- **Foydalanuvchi Monitoring**: Sessiya holati va faollik kuzatuvi
- **Ommaviy Operatsiyalar**: Samarali ko'p foydalanuvchi boshqaruvi

## 🏗️ Arxitektura

```
tgsecret/
├── 📁 bot/                    # Telegram Bot Komponentlari
│   ├── 🔧 handlers.py         # Xabar va callback ishlovchilari
│   ├── ⌨️ keyboards.py        # Interaktiv klaviatura tartiblar
│   ├── 🔐 session_creator.py  # Sessiya boshqaruv mantiq
│   ├── 🎙️ transcribe_handler.py # Audio transkript tizimi
│   ├── ⚙️ admin_commands.py   # Ma'muriy funksiyalar
│   └── 📝 constants.py        # Bot konstantalar va xabarlar
├── 📁 userbot/               # Userbot Asosiy Tizim
│   ├── 🚀 main.py            # Userbot kirish nuqtasi
│   ├── 🔌 loader.py          # Dinamik modul yuklovchi
│   └── 📁 modules/           # Xususiyat Modullari
│       ├── 🤖 ai_chat.py     # AI suhbat tizimi
│       ├── ❓ help.py         # Yordam va hujjatlar
│       └── 🎵 voice_to_text.py # Audio transkript moduli
├── 📁 sessions/              # Foydalanuvchi sessiya saqlash (avto-yaratiladi)
├── 🔧 main.py               # Dastur kirish nuqtasi
├── ⚙️ config.py             # Konfiguratsiya boshqaruvi
├── 📋 requirements.txt      # Python bog'liqliklar
└── 📖 README.md             # Bu hujjat
```

## 🚀 Tezkor Boshlash

### Talablar
- **Python 3.8+** (Tavsiya: Python 3.11+)
- **Telegram Bot Token** ([@BotFather](https://t.me/BotFather) dan oling)
- **Telegram API Ma'lumotlari** ([my.telegram.org](https://my.telegram.org) dan oling)
- **Groq API Kaliti** (Ixtiyoriy, [groq.com](https://groq.com) dan oling)

### O'rnatish

1. **Repositoriyani Klonlash**
   ```bash
   git clone https://github.com/islombek4642/tgsecret.git
   cd tgsecret
   ```

2. **Virtual Muhit Yaratish va Faollashtirish**
   ```bash
   # Virtual muhit yaratish
   python -m venv venv
   
   # Windows uchun faollashtirish
   venv\Scripts\activate
   
   # Linux/Mac uchun faollashtirish
   source venv/bin/activate
   ```

3. **Bog'liqliklarni O'rnatish**
   ```bash
   pip install -r requirements.txt
   ```

4. **Muhit Konfiguratsiyasi**
   `.env` fayl yarating:
   ```env
   # Majburiy Sozlamalar
   BOT_TOKEN=botfather_dan_olingan_token
   API_ID=my_telegram_org_dan_api_id
   API_HASH=my_telegram_org_dan_api_hash
   OWNER_ID=sizning_telegram_user_id
   
   # Ixtiyoriy Sozlamalar
   GROQ_API_KEY=ai_xususiyatlari_uchun_groq_kaliti
   AUTO_SLEEP_HOURS=12
   REQUIRED_CHANNEL=@kanal1,@kanal2  # Vergul bilan ajratilgan
   ```

5. **Tizimni Ishga Tushirish**
   ```bash
   python main.py
   ```

## 📱 Foydalanish Qo'llanmasi

### Boshlang'ich Sozlash
1. **Tizimni Ishga Tushirish**: `python main.py` ni ishga tushiring
2. **Telegramni Oching**: Botingizga xabar yuboring
3. **Boshqaruv Paneliga Kirish**: `/start` buyrug'ini yuboring
4. **Akkauntni Ulash**: "🔗 Akkaunt ulash" tugmasini bosing
5. **Autentifikatsiya**: Telefon raqam va tasdiqlash kodini kiriting
6. **Userbotni Faollashtirish**: "🚀 Ishga tushirish" tugmasini bosing

### Bot Buyruqlari
| Buyruq | Tavsif |
|--------|--------|
| `/start` | Asosiy boshqaruv paneli |
| `/admin` | Admin paneli (faqat egasi) |
| `/transcribe` | Audio transkript ma'lumoti |

### Userbot Buyruqlari
| Buyruq | Funksiya | Misol |
|--------|----------|-------|
| `.ask <savol>` | AI suhbat | `.ask Python nima?` |
| `.transcribe` | Audio transkript | Ovozli xabarga javob |
| `.help` | Buyruqlar ro'yxati | `.help` |

### Boshqaruv Paneli
- **🔗 Akkaunt ulash**: Telegram akkauntni ulash
- **🚀 Ishga tushirish**: Userbot nusxasini ishga tushirish
- **⏰ Qayta ishga tushirish**: Userbotni qayta ishga tushirish
- **📊 Holat**: Tizim holatini tekshirish
- **🚪 Chiqish**: Chiqish va tozalash

## ⚙️ Konfiguratsiya

### Muhit O'zgaruvchilari

| O'zgaruvchi | Majburiy | Tavsif | Misol |
|-------------|----------|--------|-------|
| `BOT_TOKEN` | ✅ | Telegram bot tokeni | `123456:ABC-DEF...` |
| `API_ID` | ✅ | Telegram API ID | `1234567` |
| `API_HASH` | ✅ | Telegram API hash | `abcdef123456...` |
| `OWNER_ID` | ✅ | Sizning Telegram foydalanuvchi ID | `987654321` |
| `GROQ_API_KEY` | ❌ | AI xususiyatlari uchun Groq API | `gsk_...` |
| `AUTO_SLEEP_HOURS` | ❌ | Avtomatik uyqu taymer (0=o'chirilgan) | `12` |
| `REQUIRED_CHANNEL` | ❌ | Majburiy obuna kanallari | `@kanal1,@kanal2` |

### Ma'lumotlarni Olish

#### 🤖 Bot Token
1. [@BotFather](https://t.me/BotFather) ga xabar yuboring
2. `/newbot` yuboring
3. Ko'rsatmalarga amal qiling
4. Tokenni nusxalang

#### 🔑 API Ma'lumotlari
1. [my.telegram.org](https://my.telegram.org) ga tashrif buyuring
2. Telefon raqamingiz bilan kiring
3. "API development tools" ga o'ting
4. Yangi dastur yarating
5. `api_id` va `api_hash` ni nusxalang

#### 👤 Foydalanuvchi ID
1. [@userinfobot](https://t.me/userinfobot) ga xabar yuboring
2. Foydalanuvchi ID ni nusxalang

#### 🧠 Groq API Kaliti
1. [groq.com](https://groq.com) ga tashrif buyuring
2. Bepul akkaunt yarating
3. API kalitlari bo'limiga o'ting
4. Yangi kalit yarating

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

## 📄 Litsenziya

Bu loyiha MIT litsenziyasi ostida chiqarilgan. Tafsilotlar uchun [LICENSE](LICENSE) faylini ko'ring.

## ⚠️ Ogohlantirish

**Ta'lim Maqsadi**: Bu dastur faqat ta'lim va shaxsiy foydalanish uchun mo'ljallangan.

**Muvofiqlik**: Foydalanuvchilar quyidagilarga rioya qilishlari kerak:
- Telegram Xizmat Shartlari
- Mahalliy qonunlar va qoidalar
- Platforma foydalanish siyosatlari
- Ma'lumotlarni himoya qilish talablari

**Javobgarlik**: Ishlab chiquvchilar bu dasturdan noto'g'ri foydalanish, qoidabuzarliklar yoki zarar natijasida yuzaga keladigan zararlar uchun javobgar emaslar.

**Qo'llab-quvvatlash**: Bu ochiq manbali loyiha "bor holatida" kafolatsiz taqdim etiladi.

## 🤝 Qo'llab-quvvatlash

- **Muammolar**: [GitHub Issues](https://github.com/islombek4642/tgsecret/issues)
- **Muhokamalar**: [GitHub Discussions](https://github.com/islombek4642/tgsecret/discussions)
- **Hujjatlar**: Bu README va kod ichidagi izohlar

---

<div align="center">

**Telegram jamoasi uchun ❤️ bilan yaratildi**

⭐ **Foydali bo'lsa, repoga yulduz qo'ying!** ⭐

</div>
