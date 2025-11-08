import telebot
import yt_dlp
import os
from youtubesearchpython import VideosSearch
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "🎵 Salom! Men sizga yordam bera olaman:\n\n"
        "🎶 Musiqa nomini yozing — men topib video va mp3 qilib yuboraman.\n"
        "🎬 Kino yoki multfilm nomini yozing — YouTube treylerini yuboraman.\n"
        "🔗 Yoki Instagram, TikTok, YouTube link yuboring — men videoni yuklab yuboraman."
    )
    bot.reply_to(message, text)

@bot.message_handler(func=lambda message: True)
def downloader(message):
    query = message.text.strip()

    # Agar foydalanuvchi link yuborsa
    if any(x in query for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        bot.reply_to(message, "📥 Yuklanmoqda, biroz kuting...")
        download_video(query, message)
    else:
        bot.reply_to(message, f"🔎 Qidirilmoqda: {query}")
        search_and_download(query, message)

def download_video(url, message):
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',  # cookie faylni shu joyga qo'yasiz
        'format': 'best',
        'noplaylist': True,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:
            bot.send_video(message.chat.id, video, caption=f"🎬 {info.get('title', 'Video')}")

        os.remove(filename)
    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

def search_and_download(query, message):
    try:
        videosSearch = VideosSearch(query, limit=1)
        result = videosSearch.result()["result"][0]
        url = result["link"]
        download_video(url, message)
    except Exception as e:
        bot.reply_to(message, f"❌ Qidirishda xato: {e}")

bot.polling()
