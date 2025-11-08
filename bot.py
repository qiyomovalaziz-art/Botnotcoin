import telebot
import os
import sqlite3
import yt_dlp

from telebot import types
from config import BOT_TOKEN, ADMIN_ID

bot = telebot.TeleBot(BOT_TOKEN)

# ====== DATABASE ======
if not os.path.exists("users.db"):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

# ====== START ======
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "🎬 Salom! Menga Instagram, YouTube yoki TikTok link yuboring — men sizga video yoki musiqani yuboraman 🎵")

# ====== ADMIN PANEL ======
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "📢 Xabar yuborish")
    bot.send_message(message.chat.id, "Admin panel:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.chat.id == ADMIN_ID)
def stats(message):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    conn.close()
    bot.send_message(message.chat.id, f"👥 Jami foydalanuvchilar: {count} ta")

@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish" and m.chat.id == ADMIN_ID)
def broadcast_start(message):
    bot.send_message(message.chat.id, "Yubormoqchi bo'lgan xabarni kiriting:")
    bot.register_next_step_handler(message, broadcast_message)

def broadcast_message(message):
    text = message.text
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    users = cur.fetchall()
    conn.close()
    sent = 0
    for user in users:
        try:
            bot.send_message(user[0], text)
            sent += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"✅ {sent} ta foydalanuvchiga yuborildi.")

# ====== LINK QABUL QILISH ======
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def download_video(message):
    url = message.text.strip()
    msg = bot.reply_to(message, "⏳ Yuklanmoqda, biroz kuting...")

    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'mp4',
        'quiet': True,
        'merge_output_format': 'mp4'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        with open(file_name, 'rb') as video:
            bot.send_video(message.chat.id, video)

        os.remove(file_name)
        bot.delete_message(message.chat.id, msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

# ====== RUN BOT ======
bot.infinity_polling()
