import os
import yt_dlp
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ChatAction
import requests

# --- CONFIG ---
BOT_TOKEN = "8053267322:AAHp65zXTZn_ZQswyLyjIc5e7bZnxogx9wM"

# --- VIDEO YUKLASH FUNKSIYASI ---
def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for f in os.listdir():
        if f.startswith("video.") and f.endswith(".mp4"):
            return f
    return None

# --- AUDIO YUKLASH FUNKSIYASI (nom bilan qidirish) ---
def download_music(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'music.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:{query}"])
    for f in os.listdir():
        if f.startswith("music.") and f.endswith(".mp3"):
            return f
    return None

# --- VIDEO yoki MUSIQA SO‘ROVNI ANIQLASH ---
def handle_message(update, context):
    text = update.message.text.strip()
    chat_id = update.message.chat_id
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    if any(x in text for x in ["instagram.com", "tiktok.com", "youtube.com", "youtu.be"]):
        update.message.reply_text("⏳ Video yuklanmoqda, biroz kuting...")
        try:
            filename = download_video(text)
            if filename:
                with open(filename, 'rb') as video:
                    context.bot.send_video(chat_id=chat_id, video=video, caption="🎬 Siz so‘ragan video tayyor!")
                os.remove(filename)
            else:
                update.message.reply_text("❌ Video yuklab bo‘lmadi.")
        except Exception as e:
            update.message.reply_text(f"Xatolik: {e}")
    else:
        update.message.reply_text("🎵 Musiqa izlanmoqda, kuting...")
        try:
            filename = download_music(text)
            if filename:
                with open(filename, 'rb') as audio:
                    context.bot.send_audio(chat_id=chat_id, audio=audio, caption=f"🎶 {text}")
                os.remove(filename)
            else:
                update.message.reply_text("❌ Musiqa topilmadi.")
        except Exception as e:
            update.message.reply_text(f"Xatolik: {e}")

# --- START KOMANDASI ---
def start(update, context):
    update.message.reply_text(
        "👋 Salom! Menga Instagram, YouTube yoki TikTok link tashlang — men sizga videoni yuboraman.\n\n"
        "Yoki shunchaki musiqa nomini yozing 🎵 — men sizga musiqani topib beraman."
    )

# --- BOTNI ISHGA TUSHURISH ---
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
