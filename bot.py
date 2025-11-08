import telebot
import os
import yt_dlp
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "🎵 Salom! Men sizga yordam bera olaman:\n\n"
                 "🎶 Musiqa nomini yozing — men YouTube’dan topib video va mp3 yuboraman.\n"
                 "🎬 Kino yoki multfilm nomini yozing — YouTube treylerini yuboraman.\n"
                 "📎 Yoki YouTube, TikTok, Instagram link yuboring — videoni yuklab yuboraman.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()

    if text.startswith("http://") or text.startswith("https://"):
        return download_video(message, text)

    # Agar foydalanuvchi faqat nom yozsa — YouTube’da qidiramiz
    msg = bot.reply_to(message, f"🔍 \"{text}\" bo‘yicha qidirilmoqda...")

    try:
        # YouTube'dan qidirish va yuklash
        search_url = f"ytsearch1:{text}"
        opts = {
            'format': 'best',
            'quiet': True,
            'outtmpl': 'video.%(ext)s',
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_url, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            video_file = ydl.prepare_filename(info)
            title = info.get("title", "Noma'lum video")

        # Audio yuklash
        audio_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'outtmpl': 'audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.extract_info(info['webpage_url'], download=True)

        # Video yuborish
        with open(video_file, 'rb') as vid:
            bot.send_video(message.chat.id, vid, caption=f"🎬 {title}")

        # Audio yuborish
        for file in os.listdir():
            if file.endswith(".mp3"):
                with open(file, 'rb') as aud:
                    bot.send_audio(message.chat.id, aud, caption=f"🎧 {title}")
                os.remove(file)
                break

        # Fayllarni tozalash
        if os.path.exists(video_file):
            os.remove(video_file)

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, msg.message_id)

def download_video(message, url):
    msg = bot.reply_to(message, "⏳ Yuklab olinmoqda...")

    try:
        opts = {
            'format': 'best',
            'quiet': True,
            'outtmpl': 'video.%(ext)s',
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)
            title = info.get("title", "Noma'lum video")

        # Audio yuklash
        audio_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'outtmpl': 'audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.extract_info(url, download=True)

        with open(video_file, 'rb') as vid:
            bot.send_video(message.chat.id, vid, caption=f"🎥 {title}")

        for file in os.listdir():
            if file.endswith(".mp3"):
                with open(file, 'rb') as aud:
                    bot.send_audio(message.chat.id, aud, caption=f"🎧 {title}")
                os.remove(file)
                break

        if os.path.exists(video_file):
            os.remove(video_file)

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {e}", message.chat.id, msg.message_id)

bot.polling(non_stop=True)
