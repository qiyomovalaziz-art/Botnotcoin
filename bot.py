import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# === Sozlamalar ===
BOT_TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"
ADMIN_ID = 7973934849
DATA_FILE = "users.json"
PAYMENT_FILE = "payments.json"

# === Fayllarni tayyorlash ===
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(PAYMENT_FILE):
    with open(PAYMENT_FILE, "w") as f:
        json.dump([], f)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Ma'lumotlarni o‘qish va yozish funksiyalari ===
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_payments():
    with open(PAYMENT_FILE, "r") as f:
        return json.load(f)

def save_payments(data):
    with open(PAYMENT_FILE, "w") as f:
        json.dump(data, f, indent=4)

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("💳 Pul yechish"), KeyboardButton("💰 Pul ishlash"))
    kb.add(KeyboardButton("💸 Hisobni to‘ldirish"), KeyboardButton("🏦 Investitsiya"))
    kb.add(KeyboardButton("⚙️ Boshqaruv"))
    return kb

# === Start komandasi ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    users = load_data()
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {
            "id": message.from_user.id,
            "balans": 0,
            "sarmoya": 0,
            "takliflar": 0,
            "kiritilgan": 0
        }
        save_data(users)

    text = (
        f"🏦 Assalomu alaykum {message.from_user.first_name}!\n\n"
        f"Sizning botdagi hisobingiz:\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Asosiy balans: {users[user_id]['balans']} so‘m\n"
        f"📊 Sarmoya: {users[user_id]['sarmoya']} so‘m\n"
        f"👥 Takliflaringiz: {users[user_id]['takliflar']} ta\n"
        f"💵 Kiritilgan pullar: {users[user_id]['kiritilgan']} so‘m\n\n"
        f"@Your_Bot_Username Official 2025"
    )
def main_menu():
    buttons = [
        [KeyboardButton(text="💳 Pul yechish"), KeyboardButton(text="💰 Pul ishlash")],
        [KeyboardButton(text="💸 Hisobni to‘ldirish"), KeyboardButton(text="🏦 Investitsiya")],
        [KeyboardButton(text="⚙️ Boshqaruv")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    

# === Admin panel ===
@dp.message(F.text == "⚙️ Boshqaruv")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz admin emassiz!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ To‘lov tizimi qo‘shish", callback_data="add_pay")],
        [InlineKeyboardButton(text="📄 To‘lov tizimlarini ko‘rish", callback_data="view_pay")],
    ])
    await message.answer("⚙️ Admin panel:", reply_markup=kb)

# === Callbacklar ===
@dp.callback_query(F.data == "add_pay")
async def add_payment(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📝 Yangi to‘lov tizimi nomini yuboring:")
    await callback.answer()
    dp.message.register(save_payment_name)

async def save_payment_name(message: types.Message):
    payments = load_payments()
    payments.append(message.text)
    save_payments(payments)
    await message.answer(f"✅ '{message.text}' tizimi qo‘shildi!")

@dp.callback_query(F.data == "view_pay")
async def view_payments(callback: types.CallbackQuery):
    payments = load_payments()
    if not payments:
        await callback.message.answer("⚠️ Hozircha to‘lov tizimi yo‘q.")
    else:
        await callback.message.answer("💳 To‘lov tizimlari:\n" + "\n".join(payments))
    await callback.answer()

# === Ishga tushirish ===
async def main():
    print("Bot ishga tushdi ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
