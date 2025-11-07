import asyncio
import json
import os
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ======================================================
# 🔹 TOKEN va ADMIN ID
# ======================================================
BOT_TOKEN = "BU_YERGA_TOKENINGNI_QO'Y"  # <-- faqat shu joyni o‘zgartirasan
ADMIN_ID = 123456789                    # <-- o‘zingning Telegram ID’ing (myidbot orqali bilasan)

# ======================================================
# 🔹 Asosiy sozlamalar
# ======================================================
CHANNELS_FILE = "channels.json"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================================================
# 🔹 Fayl funksiyalari
# ======================================================
def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "w") as f:
            json.dump([], f)
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=4)

# ======================================================
# 🔹 /start komandasi
# ======================================================
@dp.message(Command("start"))
async def start(message: types.Message):
    channels = load_channels()
    if not channels:
        return await message.answer("❌ Hozircha majburiy kanal qo‘shilmagan.")
    text = "📢 Quyidagi kanallarga obuna bo‘ling:\n\n"
    buttons = []
    for ch in channels:
        text += f"➡️ {ch['name']} — {ch['link']}\n"
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['name']}", url=ch['link'])])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")])
    await message.answer(
        f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
        f"{text}\nObuna bo‘lgach, <b>Tekshirish</b> tugmasini bosing 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ======================================================
# 🔹 Obuna tekshirish
# ======================================================
@dp.callback_query(F.data == "check_subs")
async def check_subs(callback: types.CallbackQuery):
    channels = load_channels()
    if not channels:
        return await callback.answer("❌ Majburiy kanal yo‘q!", show_alert=True)
    all_subscribed = True
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["username"], user_id=callback.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                all_subscribed = False
                break
        except:
            all_subscribed = False
            break
    if all_subscribed:
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(
            KeyboardButton("🛒 Buyurtma berish"),
            KeyboardButton("🎮 O‘yinlar"),
            KeyboardButton("💰 Hisobni to‘ldirish"),
            KeyboardButton("💬 Adminga yozish")
        )
        await callback.message.answer("✅ Obuna tasdiqlandi!\nMenyudan tanlang:", reply_markup=kb)
    else:
        await callback.answer("⚠️ Avval barcha kanallarga obuna bo‘ling!", show_alert=True)

# ======================================================
# 🔹 Admin panel
# ======================================================
@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz.")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Kanal qo‘shish", "➖ Kanal o‘chirish")
    kb.add("📋 Kanallar ro‘yxati", "🔙 Ortga")
    await message.answer("🔧 Admin panelga xush kelibsiz:", reply_markup=kb)

# ➕ Qo‘shish
@dp.message(F.text == "➕ Kanal qo‘shish")
async def add_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🆕 Kanalni quyidagicha kiriting:\n\n@username | https://t.me/username")

    @dp.message()
    async def save_new_channel(msg: types.Message):
        if "|" not in msg.text:
            return await msg.answer("❌ Format xato! Masalan:\n@CuruptoUZ | https://t.me/CuruptoUZ")
        username, link = msg.text.split("|")
        username, link = username.strip(), link.strip()
        channels = load_channels()
        channels.append({"username": username, "link": link, "name": username.replace("@", "")})
        save_channels(channels)
        await msg.answer("✅ Kanal qo‘shildi!")

# ➖ O‘chirish
@dp.message(F.text == "➖ Kanal o‘chirish")
async def remove_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        return await message.answer("📭 Hech qanday kanal yo‘q.")
    text = "🗑 O‘chirish uchun kanal username yozing:\n\n"
    for ch in channels:
        text += f"➡️ {ch['username']}\n"
    await message.answer(text)

    @dp.message()
    async def delete_channel(msg: types.Message):
        username = msg.text.strip()
        channels = load_channels()
        new_channels = [c for c in channels if c["username"] != username]
        if len(channels) != len(new_channels):
            save_channels(new_channels)
            await msg.answer("✅ Kanal o‘chirildi!")
        else:
            await msg.answer("❌ Bunday kanal topilmadi.")

# 📋 Ro‘yxat
@dp.message(F.text == "📋 Kanallar ro‘yxati")
async def list_channels(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        return await message.answer("📭 Hech qanday kanal yo‘q.")
    text = "📋 Majburiy kanallar:\n\n"
    for ch in channels:
        text += f"{ch['username']} — {ch['link']}\n"
    await message.answer(text)

# ======================================================
# 🔹 Asosiy funksiyalar
# ======================================================
@dp.message(F.text == "🎮 O‘yinlar")
async def games(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎲 Qura tashlash", "🏀 Basketbol", "🔙 Ortga")
    await message.answer("🎮 O‘yin tanlang:", reply_markup=kb)

@dp.message(F.text == "🎲 Qura tashlash")
async def dice(message: types.Message):
    await message.answer(f"🎲 Chiqqan son: {random.randint(1,6)}")

@dp.message(F.text == "🏀 Basketbol")
async def basketball(message: types.Message):
    await message.answer(random.choice(["🏀 500 so‘m yutding!", "😢 Yutqazding!", "🎁 Bonus ol!")])

@dp.message(F.text == "🛒 Buyurtma berish")
async def order(message: types.Message):
    await message.answer("🛍 Buyurtmangizni yozing, admin tez orada javob beradi.")

@dp.message(F.text == "💬 Adminga yozish")
async def to_admin(message: types.Message):
    await message.answer("✍️ Xabaringizni yozing, adminga yuboraman.")

    @dp.message()
    async def forward_msg(msg: types.Message):
        if msg.from_user.id != ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"📩 @{msg.from_user.username} dan:\n{msg.text}")
            await msg.answer("✅ Xabar yuborildi!")

# ======================================================
# 🔹 Run
# ======================================================
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
