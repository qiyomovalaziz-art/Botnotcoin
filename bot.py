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

    if any(x in query for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        bot.reply_to(message, "📥 Yuklanmoqda, biroz kuting...")
        download_video_and_audio(query, message)
    else:
        bot.reply_to(message, f"🔎 Qidirilmoqda: {query}")
        search_and_download(query, message)

def download_video_and_audio(url, message):
    video_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',  # ixtiyoriy
        'format': 'best',
        'noplaylist': True,
        'quiet': True
    }

    audio_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        # VIDEO yuklash
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)

        with open(video_file, 'rb') as video:
            bot.send_video(message.chat.id, video, caption=f"🎬 {info.get('title', 'Video')}")

        os.remove(video_file)

        # AUDIO (mp3) yuklash
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_file = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"

        with open(audio_file, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, caption=f"🎧 {info.get('title', 'Audio')}")

        os.remove(audio_file)

    except Exception as e:
        bot.reply_to(message, f"❌ Xatolik: {e}")

def search_and_download(query, message):
    try:
        videosSearch = VideosSearch(query, limit=1)
        result = videosSearch.result()["result"][0]
        url = result["link"]
        download_video_and_audio(url, message)
    except Exception as e:
        bot.reply_to(message, f"❌ Qidirishda xato: {e}")

bot.polling()
