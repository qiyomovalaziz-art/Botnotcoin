import telebot
import os
import yt_dlp
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🎬 Salom! Menga YouTube, TikTok yoki Instagram link yuboring.\n"
        "Men sizga video va audio qilib yuboraman 🎵"
    )

@bot.message_handler(func=lambda message: True)
def download_media(message):
    url = message.text.strip()

    # Link to‘g‘riligini tekshirish
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "❗ Iltimos, to‘g‘ri video link yuboring.")
        return

    msg = bot.reply_to(message, "⏳ Yuklab olinmoqda, biroz kuting...")

    try:
        # === Video yuklab olish ===
        video_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)

        # === Audio yuklab olish ===
        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.extract_info(url, download=True)

        # === Fayl nomini tayyorlash ===
        title = info.get("title", "Noma’lum nom")
        artist = info.get("uploader", "Noma’lum ijrochi")

        # === Video yuborish ===
        with open(video_file, 'rb') as vid:
            bot.send_video(
                message.chat.id,
                vid,
                caption=f"🎥 *{title}*\n👤 {artist}",
                parse_mode='Markdown'
            )

        # === Audio faylni topish ===
        audio_file = None
        for file in os.listdir():
            if file.endswith(".mp3"):
                audio_file = file
                break

        # === Audio yuborish ===
        if audio_file:
            with open(audio_file, 'rb') as aud:
                bot.send_audio(
                    message.chat.id,
                    aud,
                    caption=f"🎧 {artist} - {title}"
                )
            os.remove(audio_file)

        # === Yuborilgan linkni o‘chirish ===
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, msg.message_id)

        # === Ortiqcha fayllarni o‘chirish ===
        if os.path.exists(video_file):
            os.remove(video_file)

    except Exception as e:
        bot.edit_message_text(
            f"❌ Xatolik: {str(e)}",
            message.chat.id,
            msg.message_id
        )

bot.polling(non_stop=True)
