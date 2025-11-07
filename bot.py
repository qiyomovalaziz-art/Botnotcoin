import asyncio
import json
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)

# ============================
# 🔧 TOKEN VA ADMIN ID
# ============================
BOT_TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"  # Bot token
ADMIN_ID = 7973934849                    # Admin ID (myidbot orqali top)

# ============================
# 🔧 FAYL YARATISH
# ============================
CHANNELS_FILE = "channels.json"
if not os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "w") as f:
        json.dump([], f)

def load_channels():
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=4)

# ============================
# 🔧 AIROGRAM ISHGA TUSHURISH
# ============================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================
# 🔹 /start komandasi
# ============================
@dp.message(Command("start"))
async def start(message: types.Message):
    channels = load_channels()
    if not channels:
        return await message.answer("❌ Hozircha majburiy kanal yo‘q.")

    text = "Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling 👇\n\n"
    buttons = []
    for ch in channels:
        text += f"📢 {ch['name']} — {ch['link']}\n"
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['name']}", url=ch['link'])])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")])

    await message.answer(
        f"Salom, <b>{message.from_user.first_name}</b> 👋\n\n{text}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# ============================
# 🔹 Obuna tekshirish
# ============================
@dp.callback_query(F.data == "check_subs")
async def check_subs(callback: types.CallbackQuery):
    channels = load_channels()
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
            KeyboardButton("📈 Statistika"),
            KeyboardButton("💬 Adminga yozish")
        )
        await callback.message.answer("✅ Obuna tasdiqlandi! Endi buyurtma bera olasiz 👇", reply_markup=kb)
    else:
        await callback.answer("⚠️ Avval barcha kanallarga obuna bo‘ling!", show_alert=True)

# ============================
# 🔹 Admin panel
# ============================
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Siz admin emassiz.")
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ Kanal qo‘shish", "➖ Kanal o‘chirish")
    kb.add("📋 Kanallar ro‘yxati")
    kb.add("🔙 Ortga")
    await message.answer("⚙️ Admin panel:", reply_markup=kb)

# ➕ Qo‘shish
@dp.message(F.text == "➕ Kanal qo‘shish")
async def add_channel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🆕 Kanalni quyidagicha kiriting:\n@username | https://t.me/username")

    @dp.message()
    async def save_new(msg: types.Message):
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
        return await message.answer("📭 Kanallar yo‘q.")
    text = "🗑 O‘chirish uchun kanal username kiriting:\n\n"
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
            await msg.answer("✅ Kanal o‘chirildi.")
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

# ============================
# 🔹 Buyurtma va aloqa
# ============================
@dp.message(F.text == "🛒 Buyurtma berish")
async def order(message: types.Message):
    await message.answer("📨 Buyurtmangizni yozing. Admin tez orada javob beradi.")

    @dp.message()
    async def send_to_admin(msg: types.Message):
        if msg.from_user.id != ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"📩 @{msg.from_user.username or msg.from_user.id} dan:\n\n{msg.text}")
            await msg.answer("✅ Buyurtmangiz yuborildi!")

@dp.message(F.text == "💬 Adminga yozish")
async def to_admin(message: types.Message):
    await message.answer("✍️ Xabaringizni yozing, adminga yuboraman.")

    @dp.message()
    async def forward(msg: types.Message):
        if msg.from_user.id != ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"💬 @{msg.from_user.username or msg.from_user.id} dan:\n{msg.text}")
            await msg.answer("✅ Xabar yuborildi!")

# ============================
# 🔹 Statistika
# ============================
@dp.message(F.text == "📈 Statistika")
async def stats(message: types.Message):
    await message.answer("👥 Hozircha statistik funksiya yo‘q, keyingi versiyada bo‘ladi.")

# ============================
# 🔹 Run bot
# ============================
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
