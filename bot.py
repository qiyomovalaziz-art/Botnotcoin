# main.py
import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)

# ---------------- CONFIG ----------------
TOKEN = "8379130776:AAFbPEBwI8Qr9T-lm7YaR98k8bXWcu2wn9g"   # token joyiga o'zingnikini qo'y
ADMIN_ID = 7973934849           # admin ID
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
WITHDRAWS_FILE = os.path.join(DATA_DIR, "withdraws.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# ---------------- INIT ----------------
os.makedirs(DATA_DIR, exist_ok=True)
for f, default in [
    (USERS_FILE, {}),
    (WITHDRAWS_FILE, []),
    (SETTINGS_FILE, {"min_withdraw": 5000})
]:
    if not os.path.exists(f):
        with open(f, "w") as fh:
            json.dump(default, fh, indent=4)

# ---------------- HELPERS ----------------
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def now_iso():
    return datetime.now().isoformat()

def get_user(uid: int) -> Dict[str, Any]:
    data = load_json(USERS_FILE)
    sid = str(uid)
    if sid not in data:
        data[sid] = {
            "id": uid,
            "balance": 1000,
            "xp": 0,
            "level": 1,
            "bonus_time": "1970-01-01T00:00:00",
            "invest": 0,
            "invests": [],
            "ref": 0,
            "games": 0,
            "wins": 0,
            "current_quiz": "",
            "awaiting_withdraw": False
        }
        save_json(USERS_FILE, data)
    return data[sid]

def update_user(uid: int, patch: Dict[str, Any]):
    data = load_json(USERS_FILE)
    sid = str(uid)
    data[sid].update(patch)
    save_json(USERS_FILE, data)

# Withdraw functions
def add_withdraw_request(uid: int, amount: int) -> Dict[str, Any]:
    withdraws = load_json(WITHDRAWS_FILE)
    req = {
        "id": str(uuid.uuid4()),
        "user_id": uid,
        "amount": amount,
        "status": "pending",
        "created_at": now_iso()
    }
    withdraws.append(req)
    save_json(WITHDRAWS_FILE, withdraws)
    return req

def update_withdraw_status(req_id: str, status: str):
    withdraws = load_json(WITHDRAWS_FILE)
    for r in withdraws:
        if r["id"] == req_id:
            r["status"] = status
            r["updated_at"] = now_iso()
            break
    save_json(WITHDRAWS_FILE, withdraws)

def get_settings():
    return load_json(SETTINGS_FILE)

def set_min_withdraw(amount: int):
    s = get_settings()
    s["min_withdraw"] = amount
    save_json(SETTINGS_FILE, s)

# ---------------- BOT INIT ----------------
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- UI ----------------
def main_menu():
    buttons = [
        [KeyboardButton(text="💰 Balans"), KeyboardButton(text="🎮 O‘yin")],
        [KeyboardButton(text="🏦 Invest"), KeyboardButton(text="🎁 Bonus")],
        [KeyboardButton(text="👥 Referal"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="💸 Pul yechish"), KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="⚙️ Admin panel")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ---------------- GAMES ----------------
QUIZ_QUESTIONS = [
    ("5 + 3 nechchi?", "8"),
    ("O‘zbekiston poytaxti?", "toshkent"),
    ("10 - 4 nechchi?", "6"),
    ("2 * 5 nechchi?", "10")
]

INVEST_PLANS = {
    "small": (1000, 10, 60),
    "medium": (5000, 15, 180),
    "large": (10000, 25, 300)
}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user = get_user(message.from_user.id)
    text = f"👋 Salom, {message.from_user.first_name}!\nBalans: {user['balance']} so‘m\nXP: {user['xp']} | Level: {user['level']}"
    await message.answer(text, reply_markup=main_menu())

# BALANCE
@dp.message(F.text == "💰 Balans")
async def balance(message: types.Message):
    u = get_user(message.from_user.id)
    await message.answer(f"💳 Balans: {u['balance']} so‘m\nLevel: {u['level']} | XP: {u['xp']}")

# GAME MENU
@dp.message(F.text == "🎮 O‘yin")
async def game_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Raqam o‘yini", callback_data="game_basic")],
        [InlineKeyboardButton(text="🎰 Slot", callback_data="game_slot")],
        [InlineKeyboardButton(text="🧩 Savol", callback_data="game_quiz")]
    ])
    await message.answer("🎮 O‘yin tanlang:", reply_markup=kb)

# BASIC GAME
@dp.callback_query(F.data == "game_basic")
async def game_basic(call: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"choose_{i}") for i in range(1, 6)]
    ])
    await call.message.answer("1–5 oralig‘ida raqam tanlang:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("choose_"))
async def choose_num(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    chosen = int(call.data.split("_")[1])
    secret = random.randint(1, 5)
    if user["balance"] < 1500:
        await call.message.answer("❌ Yetarli mablag‘ yo‘q.")
        return await call.answer()
    if chosen == secret:
        user["balance"] += 10000
        msg = f"🎉 To‘g‘ri! +10 000 so‘m (raqam {secret})"
    else:
        user["balance"] -= 1500
        msg = f"😢 Afsus! Raqam {secret} edi. −1 500 so‘m"
    update_user(call.from_user.id, user)
    await call.message.answer(msg)
    await call.answer()

# SLOT GAME
@dp.callback_query(F.data == "game_slot")
async def slot(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    if user["balance"] < 1500:
        await call.message.answer("❌ Pul yetarli emas.")
        return await call.answer()
    emojis = ["🍒", "🍋", "💎", "⭐", "7️⃣"]
    s = [random.choice(emojis) for _ in range(3)]
    if s[0] == s[1] == s[2]:
        user["balance"] += 10000
        msg = f"🎰 {' | '.join(s)}\n🎉 Yutdingiz +10 000 so‘m!"
    else:
        user["balance"] -= 1500
        msg = f"🎰 {' | '.join(s)}\n❌ Yutqazdingiz −1 500 so‘m"
    update_user(call.from_user.id, user)
    await call.message.answer(msg)
    await call.answer()

# QUIZ
@dp.callback_query(F.data == "game_quiz")
async def quiz_start(call: types.CallbackQuery):
    q, a = random.choice(QUIZ_QUESTIONS)
    user = get_user(call.from_user.id)
    user["current_quiz"] = a.lower()
    update_user(call.from_user.id, user)
    await call.message.answer(f"🧩 Savol: {q}\n✍️ Javobni yozing.")
    await call.answer()

@dp.message()
async def message_handler(message: types.Message):
    user = get_user(message.from_user.id)
    text = message.text.strip().lower()

    # QUIZ CHECK
    if user.get("current_quiz"):
        correct = user["current_quiz"]
        user["current_quiz"] = ""
        if text == correct:
            user["balance"] += 10000
            msg = "🎉 To‘g‘ri! +10 000 so‘m"
        else:
            user["balance"] -= 1500
            msg = f"❌ Noto‘g‘ri! To‘g‘ri javob: {correct}"
        update_user(message.from_user.id, user)
        await message.answer(msg)
        return

    # WITHDRAW CHECK
    if user.get("awaiting_withdraw"):
        if not text.isdigit():
            return await message.answer("Faqat son kiriting.")
        amount = int(text)
        settings = get_settings()
        min_w = settings.get("min_withdraw", 5000)
        if amount < min_w:
            return await message.answer(f"Minimal {min_w} so‘m.")
        if amount > user["balance"]:
            return await message.answer("Balansda mablag‘ yetarli emas.")
        req = add_withdraw_request(message.from_user.id, amount)
        user["awaiting_withdraw"] = False
        update_user(message.from_user.id, user)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{req['id']}"),
             InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{req['id']}")]
        ])
        await bot.send_message(ADMIN_ID, f"Yangi so‘rov: {amount} so‘m", reply_markup=kb)
        return await message.answer("So‘rov yuborildi, admin tasdiqlaydi.")

# ADMIN CALLBACKS
@dp.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def admin_action(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Admin emassiz!", show_alert=True)
    data = call.data
    action, reqid = data.split("_", 1)
    withdraws = load_json(WITHDRAWS_FILE)
    req = next((r for r in withdraws if r["id"] == reqid), None)
    if not req:
        return await call.message.answer("So‘rov topilmadi.")
    uid = req["user_id"]
    amount = req["amount"]
    if action == "approve":
        user = get_user(uid)
        if user["balance"] < amount:
            update_withdraw_status(reqid, "failed")
            return await call.message.answer("Balans yetarli emas.")
        user["balance"] -= amount
        update_user(uid, user)
        update_withdraw_status(reqid, "approved")
        await bot.send_message(uid, f"✅ {amount} so‘m yechildi.")
        await call.message.answer("Tasdiqlandi.")
    else:
        update_withdraw_status(reqid, "rejected")
        await bot.send_message(uid, "❌ So‘rovingiz rad etildi.")
        await call.message.answer("Rad etildi.")
    await call.answer()

# RUN
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
