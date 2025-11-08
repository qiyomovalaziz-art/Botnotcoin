import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8347087773:AAFuMVzJIdPxg-iujpOXLw_Zb-CnBG5PcTw"  # bu yerga bot tokeningizni yozing

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Menga Instagram, TikTok yoki YouTube link yuboring 🎥")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("📥 Video yuklanmoqda, biroz kuting...")

    try:
        ydl_opts = {
            "outtmpl": "video.%(ext)s",
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".m4a", ".mp4")

        await update.message.reply_video(video=open(filename, "rb"))
        os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

print("Bot ishga tushdi...")
app.run_polling()
