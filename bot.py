import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    KeyboardButton, ReplyKeyboardMarkup
)

# === Sozlamalar ===
BOT_TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"
ADMIN_ID = 7973934849
USERS_FILE = "users.json"
PAYMENTS_FILE = "payments.json"

# === Fayllarni tayyorlash ===
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(PAYMENTS_FILE):
    with open(PAYMENTS_FILE, "w") as f:
        json.dump([], f)

# === Fayl funksiyalari ===
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_payments():
    with open(PAYMENTS_FILE, "r") as f:
        return json.load(f)

def save_payments(data):
    with open(PAYMENTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# === Bot obyektlari ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Asosiy menyu ===
def main_menu():
    buttons = [
        [KeyboardButton(text="💳 Pul yechish"), KeyboardButton(text="💰 Pul ishlash")],
        [KeyboardButton(text="💸 Hisobni to‘ldirish"), KeyboardButton(text="🏦 Investitsiya")],
        [KeyboardButton(text="⚙️ Boshqaruv")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# === Start komandasi ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {
            "balans": 0,
            "sarmoya": 0,
            "takliflar": 0,
            "kiritilgan": 0
        }
        save_users(users)

    text = (
        f"🏦 Assalomu alaykum, {message.from_user.first_name}!\n\n"
        f"📋 Sizning hisob ma’lumotlaringiz:\n"
        f"🆔 ID: {user_id}\n"
        f"💰 Asosiy balans: {users[user_id]['balans']} so‘m\n"
        f"💼 Sarmoya: {users[user_id]['sarmoya']} so‘m\n"
        f"👥 Takliflar: {users[user_id]['takliflar']} ta\n"
        f"💵 Kiritilgan: {users[user_id]['kiritilgan']} so‘m\n\n"
        f"@Your_Bot_Username Official 2025"
    )

    await message.answer(text, reply_markup=main_menu())

# === Pul yechish ===
@dp.message(F.text == "💳 Pul yechish")
async def withdraw_money(message: types.Message):
    payments = load_payments()
    if payments:
        pay_list = "\n".join([f"• {p}" for p in payments])
    else:
        pay_list = "⚠️ Hozircha to‘lov tizimi qo‘shilmagan!"
    await message.answer(f"💸 Pul yechish tizimlari:\n{pay_list}")

# === Hisobni to‘ldirish ===
@dp.message(F.text == "💸 Hisobni to‘ldirish")
async def deposit_money(message: types.Message):
    await message.answer("💵 Hisobni to‘ldirish uchun admin qo‘shgan tizimlardan foydalaning.")

# === Pul ishlash ===
@dp.message(F.text == "💰 Pul ishlash")
async def earn_money(message: types.Message):
    await message.answer("💼 Pul ishlash bo‘limi hozircha ishlab chiqilmoqda.")

# === Investitsiya ===
@dp.message(F.text == "🏦 Investitsiya")
async def invest_menu(message: types.Message):
    await message.answer("📈 Investitsiya funksiyasi yaqin orada qo‘shiladi!")

# === Admin panel ===
@dp.message(F.text == "⚙️ Boshqaruv")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz admin emassiz!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ To‘lov tizimi qo‘shish", callback_data="add_payment")],
        [InlineKeyboardButton(text="📋 Tizimlarni ko‘rish", callback_data="view_payments")]
    ])
    await message.answer("⚙️ Admin panel:", reply_markup=kb)

# === Callbacklar ===
@dp.callback_query(F.data == "add_payment")
async def add_payment(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("✍️ Yangi to‘lov tizimi nomini yuboring:")
    dp.message.register(save_payment_name)
    await callback.answer()

async def save_payment_name(message: types.Message):
    payments = load_payments()
    payments.append(message.text)
    save_payments(payments)
    await message.answer(f"✅ '{message.text}' tizimi qo‘shildi!")

@dp.callback_query(F.data == "view_payments")
async def view_payments(callback: types.CallbackQuery):
    payments = load_payments()
    if not payments:
        await callback.message.answer("⚠️ Tizimlar mavjud emas.")
    else:
        await callback.message.answer("💳 Tizimlar ro‘yxati:\n" + "\n".join(payments))
    await callback.answer()

# === Botni ishga tushirish ===
async def main():
    print("✅ Bot ishga tushdi va ishlamoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
