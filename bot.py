import telebot
import os
import yt_dlp
from youtubesearchpython import VideosSearch
from config import BOT_TOKEN

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "🎬 Salom! Men sizga yordam bera olaman:\n\n"
                 "🎵 Musiqa nomini yozing — men topib video va mp3 qilib yuboraman.\n"
                 "🎥 Kino yoki multfilm nomini yozing — YouTube treylerini yuboraman.\n"
                 "📎 Yoki Instagram, TikTok, YouTube link yuboring — men videoni yuklab yuboraman.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()

    # link tekshirish
    if text.startswith("http://") or text.startswith("https://"):
        return download_video(message, text)

    # nom bo‘yicha qidirish
    search = VideosSearch(text, limit=1)
    results = search.result()

    if not results or len(results['result']) == 0:
        bot.reply_to(message, "❌ Hech narsa topilmadi. Iltimos, boshqa nom kiriting.")
        return

    video = results['result'][0]
    video_title = video['title']
    video_url = video['link']
    thumbnail = video['thumbnails'][0]['url']

    caption = f"🎬 <b>{video_title}</b>\n🔗 {video_url}"
    bot.send_photo(message.chat.id, thumbnail, caption=caption, parse_mode="HTML")

    # YouTube dan video va audio yuklash
    download_video(message, video_url)

def download_video(message, url):
    msg = bot.reply_to(message, "⏳ Yuklab olinmoqda...")

    try:
        video_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)
            title = info.get("title", "Noma'lum video")

        # audio yuklash
        audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.%(ext)s',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            ydl.extract_info(url, download=True)

        # video yuborish
        with open(video_file, 'rb') as vid:
            bot.send_video(message.chat.id, vid, caption=f"🎥 {title}")

        # audio yuborish
        for file in os.listdir():
            if file.endswith(".mp3"):
                with open(file, 'rb') as aud:
                    bot.send_audio(message.chat.id, aud, caption=f"🎧 {title}")
                os.remove(file)
                break

        # fayllarni tozalash
        if os.path.exists(video_file):
            os.remove(video_file)

        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Xatolik: {str(e)}", message.chat.id, msg.message_id)

bot.polling(non_stop=True)
