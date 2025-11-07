import asyncio
import json
import os
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton
)

# === Sozlamalar ===
BOT_TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"
ADMIN_ID = 7973934849
USERS_FILE = "users.json"
PAYMENTS_FILE = "payments.json"

# === Fayllarni yaratish ===
for f in [USERS_FILE, PAYMENTS_FILE]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            json.dump({} if f == USERS_FILE else [], file)

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

# === Bot ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === Asosiy menyu ===
def main_menu():
    buttons = [
        [KeyboardButton(text="💰 Balansim"), KeyboardButton(text="🎁 Bonus olish")],
        [KeyboardButton(text="🏦 Investitsiya"), KeyboardButton(text="💳 Pul yechish")],
        [KeyboardButton(text="⚙️ Boshqaruv")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# === /start komandasi ===
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {
            "balans": 1000,  # yangi foydalanuvchiga boshlang‘ich bonus
            "sarmoya": 0,
            "bonus_vaqti": "2000-01-01 00:00:00"
        }
        save_users(users)
        await message.answer("🎉 Yangi foydalanuvchi sifatida sizga 1000 so‘m bonus berildi!")

    user = users[user_id]
    text = (
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n\n"
        f"💼 <b>Hisobingiz:</b>\n"
        f"💰 Balans: <b>{user['balans']:,} so‘m</b>\n"
        f"🏦 Sarmoya: <b>{user['sarmoya']:,} so‘m</b>\n\n"
        f"🔥 Har kuni bonus oling va sarmoyani oshiring!"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu())

# === Balansni ko‘rish ===
@dp.message(F.text == "💰 Balansim")
async def my_balance(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)
    user = users.get(user_id, {})
    await message.answer(
        f"💳 Sizning balansingiz: <b>{user.get('balans', 0):,} so‘m</b>\n"
        f"🏦 Sarmoya: <b>{user.get('sarmoya', 0):,} so‘m</b>",
        parse_mode="HTML"
    )

# === Bonus olish ===
@dp.message(F.text == "🎁 Bonus olish")
async def get_bonus(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)
    user = users[user_id]
    last_bonus = datetime.strptime(user["bonus_vaqti"], "%Y-%m-%d %H:%M:%S")
    now = datetime.now()

    if now - last_bonus < timedelta(hours=24):
        remaining = 24 - (now - last_bonus).seconds // 3600
        await message.answer(f"⏰ Siz allaqachon bonus olgansiz!\nYana {remaining} soatdan keyin urinib ko‘ring.")
    else:
        bonus = random.randint(300, 800)
        user["balans"] += bonus
        user["bonus_vaqti"] = now.strftime("%Y-%m-%d %H:%M:%S")
        save_users(users)
        await message.answer(f"🎉 Tabriklaymiz! Sizga <b>{bonus:,} so‘m</b> bonus berildi!", parse_mode="HTML")

# === Investitsiya qilish ===
@dp.message(F.text == "🏦 Investitsiya")
async def invest_money(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)
    user = users[user_id]
    if user["balans"] < 1000:
        await message.answer("⚠️ Investitsiya qilish uchun kamida 1000 so‘m kerak!")
        return
    invest_sum = 500
    user["balans"] -= invest_sum
    foyda = random.randint(700, 1000)
    user["balans"] += foyda
    save_users(users)
    await message.answer(
        f"📈 Siz {invest_sum} so‘m sarmoya kiritdingiz va {foyda - invest_sum} so‘m foyda oldingiz!\n"
        f"💰 Yangi balans: <b>{user['balans']:,} so‘m</b>", parse_mode="HTML"
    )

# === Pul yechish ===
@dp.message(F.text == "💳 Pul yechish")
async def withdraw_money(message: types.Message):
    payments = load_payments()
    pay_list = "\n".join([f"• {p}" for p in payments]) or "⚠️ To‘lov tizimi mavjud emas."
    await message.answer(f"💸 Pul yechish uchun tizim tanlang:\n{pay_list}")

# === Admin panel ===
@dp.message(F.text == "⚙️ Boshqaruv")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Siz admin emassiz!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Tizim qo‘shish", callback_data="add_pay")],
        [InlineKeyboardButton(text="📋 Tizimlar ro‘yxati", callback_data="view_pay")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar soni", callback_data="user_count")]
    ])
    await message.answer("👑 Admin panel:", reply_markup=kb)

# === Callbacklar ===
@dp.callback_query(F.data == "add_pay")
async def add_pay(callback: types.CallbackQuery):
    await callback.message.answer("✍️ Yangi to‘lov tizimi nomini yuboring:")
    dp.message.register(save_payment_name)
    await callback.answer()

async def save_payment_name(message: types.Message):
    payments = load_payments()
    payments.append(message.text)
    save_payments(payments)
    await message.answer(f"✅ '{message.text}' tizimi qo‘shildi!")

@dp.callback_query(F.data == "view_pay")
async def view_pay(callback: types.CallbackQuery):
    payments = load_payments()
    if payments:
        await callback.message.answer("💳 To‘lov tizimlari:\n" + "\n".join(payments))
    else:
        await callback.message.answer("⚠️ Tizimlar mavjud emas.")
    await callback.answer()

@dp.callback_query(F.data == "user_count")
async def user_count(callback: types.CallbackQuery):
    users = load_users()
    await callback.message.answer(f"👥 Foydalanuvchilar soni: <b>{len(users)}</b>", parse_mode="HTML")
    await callback.answer()

# === Ishga tushirish ===
async def main():
    print("🚀 Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
