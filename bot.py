import os
import yt_dlp
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = "8053267322:AAHp65zXTZn_ZQswyLyjIc5e7bZnxogx9wM"

# --- Video yuklab olish funksiyasi ---
def download_video(url):
    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for f in os.listdir():
        if f.startswith("video.") and f.endswith(".mp4"):
            return f
    return None

# --- Musiqa yuklab olish (nom bilan qidirish) ---
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

# --- /start komandasi ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Menga Instagram, TikTok yoki YouTube link tashlang — men sizga videoni yuboraman.\n\n"
        "Yoki shunchaki musiqa nomini yozing 🎵 — men sizga musiqani topib beraman."
    )

# --- Asosiy xabarlarni qayta ishlash ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if any(x in text for x in ["instagram.com", "tiktok.com", "youtube.com", "youtu.be"]):
        await update.message.reply_text("⏳ Video yuklanmoqda, biroz kuting...")
        try:
            filename = download_video(text)
            if filename:
                await update.message.reply_video(video=open(filename, 'rb'), caption="🎬 Siz so‘ragan video tayyor!")
                os.remove(filename)
            else:
                await update.message.reply_text("❌ Video yuklab bo‘lmadi.")
        except Exception as e:
            await update.message.reply_text(f"Xatolik: {e}")
    else:
        await update.message.reply_text("🎵 Musiqa izlanmoqda, kuting...")
        try:
            filename = download_music(text)
            if filename:
                await update.message.reply_audio(audio=open(filename, 'rb'), caption=f"🎶 {text}")
                os.remove(filename)
            else:
                await update.message.reply_text("❌ Musiqa topilmadi.")
        except Exception as e:
            await update.message.reply_text(f"Xatolik: {e}")

# --- Asosiy ishga tushirish ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
