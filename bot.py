import asyncio
import logging
import json
import os
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# 🔹 Token va admin ID
BOT_TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"   # <-- faqat shu joyni to‘ldirasan
ADMIN_ID = 7973934849                     # <-- o‘zingning Telegram ID’ing

# 🔹 Fayl nomi (kanallar saqlanadigan)
CHANNELS_FILE = "channels.json"

# 🔹 Log
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================================
# 🔹 Kanal fayl boshqaruvi
# ============================================================

def load_channels():
    """Kanallarni fayldan o‘qish"""
    if not os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "w") as f:
            json.dump([], f)
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)

def save_channels(channels):
    """Kanallarni faylga yozish"""
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=4)

# ============================================================
# 🔹 Start komandasi
# ============================================================

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    channels = load_channels()
    if not channels:
        await message.answer("❌ Hozircha majburiy kanal qo‘shilmagan.")
    else:
        text = "📢 Quyidagi kanallarga obuna bo‘ling:\n\n"
        kb = []
        for ch in channels:
            text += f"➡️ {ch['name']} ({ch['link']})\n"
            kb.append([InlineKeyboardButton(text=f"📢 {ch['name']}", url=ch['link'])])
        kb.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")])
        markup = InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(
            f"Salom, <b>{message.from_user.first_name}</b>! 👋\n\n"
            f"{text}\nObuna bo‘lgach, <b>Tekshirish</b> tugmasini bosing 👇",
            parse_mode="HTML",
            reply_markup=markup
        )

# ============================================================
# 🔹 Obunani tekshirish
# ============================================================

@dp.callback_query(lambda c: c.data == "check_subs")
async def check_subscription(callback: types.CallbackQuery):
    channels = load_channels()
    if not channels:
        await callback.answer("❌ Hozircha majburiy kanal yo‘q!", show_alert=True)
        return

    all_subscribed = True
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["username"], user_id=callback.from_user.id)
            if member.status not in ["member", "administrator", "creator"]:
                all_subscribed = False
                break
        except Exception as e:
            print("Xato:", e)
            all_subscribed = False
            break

    if all_subscribed:
        menu = ReplyKeyboardMarkup(resize_keyboard=True)
        menu.add(
            KeyboardButton("🛒 Buyurtma berish"),
            KeyboardButton("🎮 O‘yinlar"),
            KeyboardButton("💰 Hisobni to‘ldirish"),
            KeyboardButton("💬 Adminga yozish")
        )
        await callback.message.answer("✅ Obuna tasdiqlandi!\nMenyudan tanlang:", reply_markup=menu)
    else:
        await callback.answer("⚠️ Avval barcha kanallarga obuna bo‘ling!", show_alert=True)

# ============================================================
# 🔹 Admin panel
# ============================================================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz.")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Kanal qo‘shish", "➖ Kanal o‘chirish", "📋 Kanallar ro‘yxati", "🔙 Ortga")
    await message.answer("🔧 Admin panel", reply_markup=kb)

# ➕ Kanal qo‘shish
@dp.message(lambda m: m.text == "➕ Kanal qo‘shish")
async def add_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🆕 Kanal username va linkni yuboring (masalan:\n@CuruptoUZ | https://t.me/CuruptoUZ)")
    
    @dp.message()
    async def save_channel(msg: types.Message):
        if "|" in msg.text:
            username, link = msg.text.split("|")
            username, link = username.strip(), link.strip()
            channels = load_channels()
            channels.append({"username": username, "link": link, "name": username.replace("@", "")})
            save_channels(channels)
            await msg.answer("✅ Kanal muvaffaqiyatli qo‘shildi!")
        else:
            await msg.answer("❌ Noto‘g‘ri format! Quyidagicha yuboring:\n@username | https://t.me/username")

# ➖ Kanal o‘chirish
@dp.message(lambda m: m.text == "➖ Kanal o‘chirish")
async def remove_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        return await message.answer("📭 Hozircha kanal yo‘q.")
    text = "🗑 O‘chirish uchun kanal username yozing:\n\n"
    for ch in channels:
        text += f"➡️ {ch['username']}\n"
    await message.answer(text)
    
    @dp.message()
    async def delete_channel(msg: types.Message):
        username = msg.text.strip()
        channels = load_channels()
        new_channels = [c for c in channels if c["username"] != username]
        if len(new_channels) != len(channels):
            save_channels(new_channels)
            await msg.answer("✅ Kanal o‘chirildi!")
        else:
            await msg.answer("❌ Bunday kanal topilmadi!")

# 📋 Kanallar ro‘yxati
@dp.message(lambda m: m.text == "📋 Kanallar ro‘yxati")
async def list_channels(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        await message.answer("📭 Hozircha kanal yo‘q.")
    else:
        text = "📋 Majburiy kanallar ro‘yxati:\n\n"
        for ch in channels:
            text += f"➡️ {ch['username']} — {ch['link']}\n"
        await message.answer(text)

# ============================================================
# 🔹 Asosiy menyu funksiyalar
# ============================================================

@dp.message(lambda m: m.text == "💬 Adminga yozish")
async def contact_admin(message: types.Message):
    await message.answer("✍️ Xabaringizni yozing, adminga yuboraman:")

    @dp.message()
    async def forward_to_admin(msg: types.Message):
        if msg.from_user.id != ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"📩 @{msg.from_user.username} dan:\n{msg.text}")
            await msg.answer("✅ Xabaringiz yuborildi!")
        else:
            await msg.answer("Admin sizsiz 😄")

@dp.message(lambda m: m.text == "🎮 O‘yinlar")
async def games_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎲 Qura tashlash", "🏀 Basketbol", "🔙 Ortga")
    await message.answer("🎮 O‘yin tanlang:", reply_markup=kb)

@dp.message(lambda m: m.text == "🎲 Qura tashlash")
async def dice_game(message: types.Message):
    x = random.randint(1, 6)
    await message.answer(f"🎲 Chiqqan son: {x}")

@dp.message(lambda m: m.text == "🏀 Basketbol")
async def basket(message: types.Message):
    result = random.choice(["200 so‘m yutding!", "Yutqazding 😢", "500 so‘m bonus!"])
    await message.answer(f"🏀 Natija: {result}")

@dp.message(lambda m: m.text == "🛒 Buyurtma berish")
async def order_cmd(message: types.Message):
    await message.answer("🛍 Buyurtmangizni yozing, tez orada admin javob beradi.")

# ============================================================
# 🔹 Botni ishga tushurish
# ============================================================

async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
