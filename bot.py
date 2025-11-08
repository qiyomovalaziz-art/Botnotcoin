import os
import asyncio
import tempfile
import logging
import requests
from pathlib import Path
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- TOKEN va API sozlamalari ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Bot token
TMDB_API_KEY = os.getenv("TMDB_API_KEY")      # ixtiyoriy, kino ma'lumotlari uchun

# --- Log sozlamalari (xatolarni ko‘rish uchun) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === 1️⃣ Kino ma'lumotini olish funksiyasi ===
def search_movie_tmdb(query: str):
    """
    TMDb API orqali kino ma'lumotini olish.
    """
    if not TMDB_API_KEY:
        return None

    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query, "language": "en-US"}
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return None

    data = r.json()
    if not data.get("results"):
        return None

    top = data["results"][0]
    return {
        "title": top.get("title"),
        "overview": top.get("overview"),
        "year": top.get("release_date", "")[:4],
        "rating": top.get("vote_average"),
        "poster": f"https://image.tmdb.org/t/p/w500{top['poster_path']}" if top.get("poster_path") else None
    }

# === 2️⃣ Instagram video yuklash funksiyasi ===
async def download_instagram(url: str, target_dir: Path):
    """
    Instagramdan video va audio yuklaydi.
    """
    video_path = target_dir / "insta_video.mp4"
    audio_path = target_dir / "insta_audio.mp3"

    # Video yuklash
    ydl_opts_video = {
        "outtmpl": str(video_path),
        "format": "best",
        "quiet": True
    }
    # Audio yuklash
    ydl_opts_audio = {
        "outtmpl": str(audio_path),
        "format": "bestaudio/best",
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    loop = asyncio.get_event_loop()

    # video yuklash
    def run_video():
        with YoutubeDL(ydl_opts_video) as ydl:
            ydl.download([url])

    # audio yuklash
    def run_audio():
        with YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([url])

    await loop.run_in_executor(None, run_video)
    await loop.run_in_executor(None, run_audio)

    return video_path, audio_path

# === 3️⃣ /start buyrug‘i ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! 👋\n"
        "Men sizga kinolar haqida ma'lumot topaman 🎬\n"
        "va Instagram linkdan video + audio olib bera olaman.\n\n"
        "Yozing:\n"
        "🔹 Kino nomi → ma'lumot chiqadi\n"
        "🔹 Instagram link → video va audio yuboraman."
    )

# === 4️⃣ Asosiy xabarlarni qayta ishlash ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Agar bu Instagram link bo‘lsa:
    if "instagram.com" in text:
        await update.message.reply_text("Instagram havolasi topildi. Yuklanmoqda...⏳")

        tmpdir = Path(tempfile.mkdtemp())
        try:
            video_path, audio_path = await download_instagram(text, tmpdir)

            if video_path.exists():
                await update.message.reply_video(video=open(video_path, "rb"))
            if audio_path.exists():
                await update.message.reply_audio(audio=open(audio_path, "rb"))

        except Exception as e:
            await update.message.reply_text(f"Xatolik yuz berdi: {e}")
        finally:
            for p in tmpdir.glob("*"):
                p.unlink()
            tmpdir.rmdir()
        return

    # Aks holda kino nomi deb qabul qilamiz
    await update.message.reply_text(f"Qidirilmoqda: {text} 🎬")
    info = search_movie_tmdb(text)

    if not info:
        await update.message.reply_text("Kino topilmadi yoki TMDB_API_KEY yo‘q 😕")
        return

    caption = (
        f"🎬 *{info['title']}* ({info['year']})\n"
        f"⭐️ Reyting: {info['rating']}\n\n"
        f"{info['overview']}"
    )

    if info["poster"]:
        await update.message.reply_photo(photo=info["poster"], caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")

# === 5️⃣ Botni ishga tushirish ===
def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN topilmadi. Iltimos .env faylga qo‘shing.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
