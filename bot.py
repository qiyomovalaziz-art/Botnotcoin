# main.py
import asyncio
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)

# ---------------- CONFIG ----------------
TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"   # <-- shu joyga tokeningizni qo'ying (yoki env orqali o'qing)
ADMIN_ID = 7973934849           # siz yagona admin
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
WITHDRAWS_FILE = os.path.join(DATA_DIR, "withdraws.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# Minimal init
os.makedirs(DATA_DIR, exist_ok=True)
for f, default in [
    (USERS_FILE, {}),
    (WITHDRAWS_FILE, []),
    (SETTINGS_FILE, {"min_withdraw": 5000})
]:
    if not os.path.exists(f):
        with open(f, "w") as fh:
            json.dump(default, fh, indent=4)

# ---------------- Helpers ----------------
def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def now_iso():
    return datetime.now().isoformat()

# User utilities
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
            "invests": [],        # list of active invests (for tracking)
            "ref": 0,
            "games": 0,
            "wins": 0,
            "current_quiz": "",   # answer for quiz if active
        }
        save_json(USERS_FILE, data)
    return data[sid]

def update_user_field(uid: int, key: str, value):
    data = load_json(USERS_FILE)
    sid = str(uid)
    data[sid][key] = value
    save_json(USERS_FILE, data)

def update_user(uid: int, patch: Dict[str, Any]):
    data = load_json(USERS_FILE)
    sid = str(uid)
    data[sid].update(patch)
    save_json(USERS_FILE, data)

# Withdraw utilities
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

# Settings
def get_settings():
    return load_json(SETTINGS_FILE)

def set_min_withdraw(amount: int):
    s = get_settings()
    s["min_withdraw"] = amount
    save_json(SETTINGS_FILE, s)

# ---------------- Bot init ----------------
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

# ---------------- Games / Core features ----------------

# Quiz bank
QUIZ_QUESTIONS = [
    ("5 + 3 nechchi?", "8"),
    ("O‘zbekiston poytaxti qayer?", "toshkent"),
    ("10 - 4 nechchi?", "6"),
    ("Dunyo okeanlari nechta?", "4"),
    ("2 * 5 nechchi?", "10"),
]

# Invest plans: (amount, percent, duration_seconds)
INVEST_PLANS = {
    "small":  (1000, 10, 60),    # 1 minute for demo
    "medium": (5000, 15, 180),   # 3 minutes
    "large":  (10000, 25, 300),  # 5 minutes
}

# Start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id)
    text = (
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n"
        f"🎁 Boshlang‘ich balans: <b>{user['balance']}</b> so‘m\n"
        f"⭐ Level: {user['level']} | XP: {user['xp']}\n\n"
        "Bot menyusi — pastdagi tugmalardan tanlang."
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")

# Balance
@dp.message(F.text == "💰 Balans")
async def show_balance(message: types.Message):
    u = get_user(message.from_user.id)
    await message.answer(
        f"💳 Balans: {u['balance']} so‘m\n"
        f"🏦 Invest (aktiv): {u['invest']} so‘m\n"
        f"🎮 O‘yinlar: {u['games']} | Yutuqlar: {u['wins']}\n"
        f"⭐ XP: {u['xp']} | Level: {u['level']}"
    )

# Game menu
@dp.message(F.text == "🎮 O‘yin")
async def game_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Oddiy (1–5)", callback_data="game_basic")],
        [InlineKeyboardButton(text="🎰 Slot", callback_data="game_slot")],
        [InlineKeyboardButton(text="🧩 Kvest", callback_data="game_quiz")]
    ])
    await message.answer("🎮 Qaysi o‘yinni tanlaysiz?", reply_markup=kb)

# Basic number game
@dp.callback_query(F.data == "game_basic")
async def game_basic_start(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    if user["balance"] < 1500:
        await call.message.answer("❌ Pul yetarli emas! O‘yin uchun kamida 1500 soʻm kerak.")
        return await call.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"basic_{i}") for i in range(1, 6)]
    ])
    await call.message.answer("🎯 1-5 oralig‘idan son tanlang:", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("basic_"))
async def game_basic_play(call: types.CallbackQuery):
    chosen = int(call.data.split("_")[1])
    secret = random.randint(1, 5)
    user = get_user(call.from_user.id)

    # Ensure ability to deduct if lose (but never negative)
    if user["balance"] < 1500:
        await call.message.answer("❌ Sizda yetarli mablag‘ yo‘q.")
        return await call.answer()

    if chosen == secret:
        # win
        user["balance"] += 10000
        user["xp"] += 10
        user["wins"] += 1
        result = f"🎉 To‘g‘ri! +10 000 so‘m. Raqam: {secret}"
    else:
        # lose
        user["balance"] = max(0, user["balance"] - 1500)
        result = f"😢 Afsus, raqam {secret} edi. −1 500 so‘m"

    user["games"] += 1
    # level up
    if user["xp"] >= user["level"] * 100:
        user["level"] += 1
        result += f"\n🏅 Siz {user['level']} darajaga ko‘tarildingiz!"

    update_user(call.from_user.id, user)
    await call.message.answer(result)
    await call.answer()

# Slot
@dp.callback_query(F.data == "game_slot")
async def game_slot_play(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    if user["balance"] < 1500:
        await call.message.answer("❌ Pul yetarli emas! Kamida 1500 so‘m kerak.")
        return await call.answer()

    emojis = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
    slots = [random.choice(emojis) for _ in range(3)]
    display = " | ".join(slots)
    if slots[0] == slots[1] == slots[2]:
        user["balance"] += 10000
        user["wins"] += 1
        msg = f"🎰 {display}\n🎉 Jackpot! +10 000 so‘m"
    else:
        user["balance"] = max(0, user["balance"] - 1500)
        msg = f"🎰 {display}\n❌ Yutqazdingiz. −1 500 so‘m"

    user["games"] += 1
    # XP reward small
    user["xp"] += 5
    if user["xp"] >= user["level"] * 100:
        user["level"] += 1
        msg += f"\n🏅 Level oshdi: {user['level']}"

    update_user(call.from_user.id, user)
    await call.message.answer(msg)
    await call.answer()

# Quiz start
@dp.callback_query(F.data == "game_quiz")
async def game_quiz_start(call: types.CallbackQuery):
    user = get_user(call.from_user.id)
    if user["balance"] < 1500:
        await call.message.answer("❌ Pul yetarli emas! Kamida 1500 so‘m kerak.")
        return await call.answer()
    q, a = random.choice(QUIZ_QUESTIONS)
    # save current correct answer to user
    user["current_quiz"] = a.lower().strip()
    update_user(call.from_user.id, user)
    await call.message.answer(f"🧩 Savol: {q}\n✍️ Javobni yozing (tekshirish uchun 1 daqiqa bor).")
    await call.answer()

# Handle quiz answers (any message)
@dp.message()
async def catch_all_messages(message: types.Message):
    # If user has active quiz answer expected
    user = get_user(message.from_user.id)
    # Only treat as quiz if current_quiz is set and message is not a command or menu text
    text = message.text.strip().lower()
    if user.get("current_quiz"):
        correct = user["current_quiz"]
        # reset field after checking
        user["current_quiz"] = ""
        if text == correct:
            user["balance"] += 10000
            user["xp"] += 15
            user["wins"] += 1
            resp = "🎉 To‘g‘ri javob! +10 000 so‘m va +15 XP"
        else:
            user["balance"] = max(0, user["balance"] - 1500)
            resp = f"❌ Noto‘g‘ri javob. To‘g‘ri javob: {correct}. −1 500 so‘m"
        user["games"] += 1
        # level check
        if user["xp"] >= user["level"] * 100:
            user["level"] += 1
            resp += f"\n🏅 Level oshdi: {user['level']}"
        update_user(message.from_user.id, user)
        await message.answer(resp)
        return

    # If not quiz, ignore here — normal menu commands handled above.
    # This avoids interfering with other flows.
    return

# ---------------- Bonus ----------------
@dp.message(F.text == "🎁 Bonus")
async def cmd_bonus(message: types.Message):
    user = get_user(message.from_user.id)
    last = datetime.fromisoformat(user.get("bonus_time", "1970-01-01T00:00:00"))
    if datetime.now() - last < timedelta(hours=24):
        remaining = timedelta(hours=24) - (datetime.now() - last)
        hours = remaining.seconds // 3600
        await message.answer(f"⏳ Bonusni {hours} soatdan keyin olishingiz mumkin.")
        return
    user["balance"] += 500
    user["bonus_time"] = now_iso()
    update_user(message.from_user.id, user)
    await message.answer("🎁 Bonus berildi: +500 so‘m!")

# ---------------- Invest ----------------
@dp.message(F.text == "🏦 Invest")
async def cmd_invest(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Kichik (1000 so‘m, 10%)", callback_data="inv_small")],
        [InlineKeyboardButton(text="📈 O‘rta (5000 so‘m, 15%)", callback_data="inv_medium")],
        [InlineKeyboardButton(text="🏦 Katta (10000 so‘m, 25%)", callback_data="inv_large")],
    ])
    await message.answer("Sarmoya rejangizni tanlang (demo vaqt bilan):", reply_markup=kb)

async def process_invest_finish(uid: int, plan_name: str, amount: int, percent: int, duration: int):
    # Wait for duration then pay profit
    await asyncio.sleep(duration)
    user = get_user(uid)
    profit = int(amount * percent / 100)
    user["balance"] += amount + profit
    # reduce invest recorded in user.invests
    user["invest"] = max(0, user.get("invest", 0) - amount)
    # remove invest record if stored
    invests = user.get("invests", [])
    invests = [it for it in invests if it.get("id") != f"{uid}_{plan_name}_{amount}"]
    user["invests"] = invests
    # save and notify
    update_user(uid, user)
    try:
        await bot.send_message(uid, f"💰 Sarmoya yakunlandi! Sizga {profit} so‘m foyda qo‘shildi.")
    except:
        pass

@dp.callback_query(F.data.startswith("inv_"))
async def inv_callback(call: types.CallbackQuery):
    plan = call.data.split("_", 1)[1]  # small/medium/large
    p = None
    if plan == "small":
        p = INVEST_PLANS["small"]
    elif plan == "medium":
        p = INVEST_PLANS["medium"]
    elif plan == "large":
        p = INVEST_PLANS["large"]
    if not p:
        await call.message.answer("Noto‘g‘ri reja tanlandi.")
        return await call.answer()
    amount, percent, duration = p
    user = get_user(call.from_user.id)
    if user["balance"] < amount:
        await call.message.answer("❌ Balansingizda mablag‘ yetarli emas.")
        return await call.answer()
    # Deduct and record invest
    user["balance"] -= amount
    user["invest"] = user.get("invest", 0) + amount
    invest_record = {"id": f"{call.from_user.id}_{plan}_{amount}", "plan": plan, "amount": amount, "percent": percent, "started": now_iso()}
    user.setdefault("invests", []).append(invest_record)
    update_user(call.from_user.id, user)
    # create background task to finish invest
    asyncio.create_task(process_invest_finish(call.from_user.id, plan, amount, percent, duration))
    await call.message.answer(f"✅ {amount} so‘m sarmoya qilindi. {percent}% foyda — kuting...")
    await call.answer()

# ---------------- Referal ----------------
@dp.message(F.text == "👥 Referal")
async def cmd_referral(message: types.Message):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start={message.from_user.id}"
    await message.answer(f"👥 Do‘stlaringizni taklif qiling, har bir kelgan user uchun 5% bonus olasiz.\n\n🔗 {link}")

# ---------------- Withdraw (user request -> admin confirm) ----------------
@dp.message(F.text == "💸 Pul yechish")
async def cmd_withdraw_request(message: types.Message):
    settings = get_settings()
    await message.answer(f"💸 Yechmoqchi bo‘lgan summangizni kiriting (minimal: {settings['min_withdraw']} so‘m).")
    # register next message handler: we'll use a simple state in file to avoid advanced FSM
    # set a temporary marker in user's data
    user = get_user(message.from_user.id)
    user["awaiting_withdraw"] = True
    update_user(message.from_user.id, user)

@dp.message()
async def handle_withdraw_amount(message: types.Message):
    # Only act if user expects withdraw input
    user = get_user(message.from_user.id)
    if not user.get("awaiting_withdraw"):
        # Already handled by quiz handler earlier or ignored.
        # We must ensure not to conflict: quiz handled above because we returned early when quiz active.
        return
    text = message.text.strip().replace(",", "")
    if not text.isdigit():
        await message.answer("❌ Iltimos faqat son kiriting.")
        return
    amount = int(text)
    settings = get_settings()
    min_w = settings.get("min_withdraw", 5000)
    if amount < min_w:
        await message.answer(f"❌ Minimal yechish summasi {min_w} so‘m. Yana urinib ko‘ring.")
        return
    if amount > user["balance"]:
        await message.answer("❌ Balansingizda bunday summa yo‘q.")
        return
    # create request, do not deduct until admin approves
    req = add_withdraw_request(message.from_user.id, amount)
    # clear awaiting flag
    user["awaiting_withdraw"] = False
    update_user(message.from_user.id, user)
    await message.answer("✅ Yechim so‘rovingiz adminga yuborildi. Tasdiqlangandan keyin pul yechiladi.")
    # notify admin with approve/reject buttons
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{req['id']}"),
         InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{req['id']}")]
    ])
    try:
        await bot.send_message(ADMIN_ID, f"📥 Yechim so‘rovi: user={message.from_user.id} amount={amount} so‘m\nID: {req['id']}", reply_markup=kb)
    except:
        pass

@dp.callback_query(F.data.startswith("approve_") | F.data.startswith("reject_"))
async def admin_decision(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Siz admin emassiz!", show_alert=True)
    data = call.data
    action, reqid = data.split("_", 1)
    withdraws = load_json(WITHDRAWS_FILE)
    req = next((r for r in withdraws if r["id"] == reqid), None)
    if not req:
        await call.message.answer("So‘rov topilmadi.")
        return await call.answer()
    if req["status"] != "pending":
        await call.message.answer("Bu so‘rov avvaldan qayta ishlangan.")
        return await call.answer()
    uid = req["user_id"]
    amount = req["amount"]
    if action == "approve":
        # deduct
        user = get_user(uid)
        if user["balance"] < amount:
            await call.message.answer("❌ Foydalanuvchida yetarli mablag‘ yo‘q - rad qilindi.")
            update_withdraw_status(reqid, "failed")
            await call.answer()
            return
        user["balance"] -= amount
        update_user(uid, user)
        update_withdraw_status(reqid, "approved")
        await call.message.answer(f"✅ So‘rov tasdiqlandi. {amount} so‘m yechildi.")
        try:
            await bot.send_message(uid, f"✅ Sizning yechish so‘rovingiz tasdiqlandi. {amount} so‘m yechildi.")
        except:
            pass
    else:
        update_withdraw_status(reqid, "rejected")
        await call.message.answer("❌ So‘rov rad etildi.")
        try:
            await bot.send_message(uid, "❌ Sizning yechish so‘rovingiz admin tomonidan rad etildi.")
        except:
            pass
    await call.answer()

# ---------------- Ranking / Stats ----------------
@dp.message(F.text == "🏆 Reyting")
async def cmd_ranking(message: types.Message):
    data = load_json(USERS_FILE)
    arr = sorted(data.values(), key=lambda u: u.get("balance", 0), reverse=True)[:10]
    if not arr:
        return await message.answer("Hozircha foydalanuvchi yo‘q.")
    text = "🏆 Top 10 boy foydalanuvchilar:\n\n"
    for i, u in enumerate(arr, 1):
        name = f"User {u.get('id')}"
        text += f"{i}. {name} — {u.get('balance',0)} so‘m\n"
    await message.answer(text)

@dp.message(F.text == "📊 Statistika")
async def cmd_stats(message: types.Message):
    data = load_json(USERS_FILE)
    total_users = len(data)
    total_balance = sum(u.get("balance", 0) for u in data.values())
    total_games = sum(u.get("games", 0) for u in data.values())
    await message.answer(
        f"📊 Umumiy statistika:\n\nFoydalanuvchilar: {total_users}\nJami balans: {total_balance} so‘m\nO‘yinlar: {total_games}"
    )

# ---------------- Admin panel ----------------
@dp.message(F.text == "⚙️ Admin panel")
async def cmd_admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton(text="📥 Yechim so‘rovlari", callback_data="admin_withdraws")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")],
        [InlineKeyboardButton(text="📢 Hammaga xabar", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📈 Statistika", callback_data="admin_stats")],
    ])
    await message.answer("👑 Admin panel:", reply_markup=kb)

@dp.callback_query(F.data == "admin_users")
async def admin_users(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Siz admin emassiz!")
    data = load_json(USERS_FILE)
    await call.message.answer(f"📋 Foydalanuvchilar soni: {len(data)}")
    await call.answer()

@dp.callback_query(F.data == "admin_withdraws")
async def admin_withdraws(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return await call.answer("Siz admin emassiz!")
    withdraws = load_json(WITHDRAWS_FILE)
    pending = [w for w in withdraws if w["status"] == "pending"]
    if not pending:
        await call.message.answer("📭 Pending so‘rovlar yo‘q.")
        return await call.answer()
    for w in pending:
        kb = InlineKeyboardMarkup(inline_keyboard=[
         
