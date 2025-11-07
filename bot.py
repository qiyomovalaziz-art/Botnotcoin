# main.py
"""
Turfabot - single-file mega bot
Features:
- Multilingual (uz/ru/en) UI
- SQLite persistence
- Balance, XP, Level
- Daily bonus
- 3 games: number guess, slot, quick quiz
- Invest plans (demo durations)
- Referral (5%)
- Withdraw requests (admin approve)
- Admin panel (stats, set min withdraw, add funds, broadcast)
- Shop, Missions, Jackpot (basic)
- Uses .env for BOT_TOKEN and ADMIN_ID
"""

import asyncio
import os
import random
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup,
    InlineKeyboardMarkup, InlineKeyboardButton
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# --- DB setup (SQLite) ---
DB_FILE = "turfabot.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    lang TEXT DEFAULT 'uz',
    balance INTEGER DEFAULT 1000,
    xp INTEGER DEFAULT 0,
    lvl INTEGER DEFAULT 1,
    last_bonus TEXT DEFAULT '',
    referrer INTEGER DEFAULT 0,
    awaiting_withdraw INTEGER DEFAULT 0,
    current_quiz TEXT DEFAULT '',
    premium INTEGER DEFAULT 0
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS invests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    percent INTEGER,
    finish_at TEXT,
    status TEXT DEFAULT 'active'
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    completed INTEGER DEFAULT 0,
    reward INTEGER DEFAULT 0
)
""")
conn.commit()

# --- Helpers ---
def now_iso():
    return datetime.utcnow().isoformat()

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if row:
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))
    return None

def ensure_user(user: types.User, ref=None):
    u = get_user(user.id)
    if u:
        return u
    cur.execute(
        "INSERT INTO users(user_id, username, first_name, lang, referrer) VALUES(?,?,?,?,?)",
        (user.id, user.username or "", user.first_name or "", "uz", ref or 0)
    )
    conn.commit()
    return get_user(user.id)

def update_user_field(uid, field, value):
    cur.execute(f"UPDATE users SET {field}=? WHERE user_id=?", (value, uid))
    conn.commit()

def add_balance(uid, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def change_balance(uid, amount):  # set relative (can be negative)
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    bal = cur.fetchone()[0]
    new = max(0, bal + amount)
    cur.execute("UPDATE users SET balance=? WHERE user_id=?", (new, uid))
    conn.commit()
    return new

def add_xp(uid, xp):
    cur.execute("SELECT xp, lvl FROM users WHERE user_id=?", (uid,))
    xp0, lvl = cur.fetchone()
    xp0 += xp
    # level rule: every 100 XP -> level up
    while xp0 >= lvl * 100:
        xp0 -= lvl * 100
        lvl += 1
    cur.execute("UPDATE users SET xp=?, lvl=? WHERE user_id=?", (xp0, lvl, uid))
    conn.commit()
    return lvl

def list_top(n=10):
    cur.execute("SELECT user_id, first_name, balance FROM users ORDER BY balance DESC LIMIT ?", (n,))
    return cur.fetchall()

# --- Bot init ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Texts (minimal translation) ---
TEXT = {
    "uz": {
        "welcome": "🇺🇿 Turfabotga xush kelibsiz! Tilni tanlang / Select language",
        "main_menu": ["💰 Balans","🎮 O‘yinlar","🎁 Bonus","👥 Referal","💸 Pul yechish","📊 Statistika","⚙️ Admin"],
        "bal": "💳 Sizning balans: {balance} so‘m\n⭐ Level: {lvl} | XP: {xp}",
        "no_money_game": "❌ Yetarli mablagʻ yoʻq. Minimal: {min} soʻm",
        "bonus_taken": "🎁 Bonus olindi: +{amt} soʻm",
        "bonus_wait": "⏳ Keyingi bonusni {hours} soatdan keyin olasiz.",
        "withdraw_sent": "✅ Yechish so‘rovingiz yuborildi. Admin tasdiqlaydi.",
        "withdraw_notify_admin": "📥 Yangi yechish so‘rovi\nUser: {uid}\nSumma: {amt}"
    },
    "ru": {
        "welcome": "🇷🇺 Добро пожаловать в Turfabot! Выберите язык",
        "main_menu": ["💰 Баланс","🎮 Игры","🎁 Бонус","👥 Реферал","💸 Вывод","📊 Статистика","⚙️ Админ"],
        "bal": "💳 Баланс: {balance} сом\n⭐ Уровень: {lvl} | XP: {xp}",
        "no_money_game": "❌ Недостаточно средств. Минимум: {min}",
        "bonus_taken": "🎁 Бонус получен: +{amt} сом",
        "bonus_wait": "⏳ Следующий бонус через {hours} часов.",
        "withdraw_sent": "✅ Запрос на вывод отправлен. Админ подтвердит.",
        "withdraw_notify_admin": "📥 Новый запрос на вывод\nUser: {uid}\nСумма: {amt}"
    },
    "en": {
        "welcome": "🇬🇧 Welcome to Turfabot! Choose language",
        "main_menu": ["💰 Balance","🎮 Games","🎁 Bonus","👥 Referral","💸 Withdraw","📊 Stats","⚙️ Admin"],
        "bal": "💳 Your balance: {balance}\n⭐ Level: {lvl} | XP: {xp}",
        "no_money_game": "❌ Not enough funds. Minimum: {min}",
        "bonus_taken": "🎁 Bonus claimed: +{amt}",
        "bonus_wait": "⏳ Next bonus in {hours} hours.",
        "withdraw_sent": "✅ Withdraw request sent. Admin will approve.",
        "withdraw_notify_admin": "📥 New withdraw request\nUser: {uid}\nAmount: {amt}"
    }
}

# --- Keyboards ---
def lang_kb():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    return kb

def main_menu_kb(lang="uz"):
    texts = TEXT[lang]["main_menu"]
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(texts[0]), KeyboardButton(texts[1])],
            [KeyboardButton(texts[2]), KeyboardButton(texts[3])],
            [KeyboardButton(texts[4]), KeyboardButton(texts[5])],
            [KeyboardButton(texts[6])]
        ], resize_keyboard=True
    )
    return kb

# --- Start / Language selection ---
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    # register user
    args = msg.text.split()
    ref = None
    if len(args) > 1:
        try:
            ref = int(args[1])
        except:
            ref = None
    ensure_user(msg.from_user, ref)
    await msg.answer(TEXT["uz"]["welcome"], reply_markup=lang_kb())

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(call: types.CallbackQuery):
    lang = call.data.split("_")[1]
    uid = call.from_user.id
    ensure_user(call.from_user)
    update_user_field(uid, "lang", lang)
    u = get_user(uid)
    await call.message.edit_text(
        f"{'🇺🇿' if lang=='uz' else '🇷🇺' if lang=='ru' else '🇬🇧'} {call.from_user.first_name}",
        reply_markup=main_menu_kb(lang)
    )
    await call.answer()

# --- Balance ---
@dp.message()
async def menu_handler(message: types.Message):
    # Route by exact button text from current language
    uid = message.from_user.id
    u = get_user(uid)
    if not u:
        u = ensure_user(message.from_user)
    lang = u.get("lang", "uz")
    texts = TEXT[lang]
    text = message.text.strip()

    # Map main menu texts
    menu = texts["main_menu"]
    # Balance
    if text == menu[0]:
        await message.answer(texts["bal"].format(balance=u["balance"], lvl=u["lvl"], xp=u["xp"]), reply_markup=main_menu_kb(lang))
        return

    # Games
    if text == menu[1]:
        # show games menu
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton("🔢 Number (1-5)"), KeyboardButton("🎰 Slot")],
            [KeyboardButton("🧠 Quiz"), KeyboardButton("🎡 Spin Wheel")],
            [KeyboardButton("⬅️ Back")]
        ], resize_keyboard=True)
        await message.answer("🎮 Choose a mini-game:", reply_markup=kb)
        return

    # Bonus
    if text == menu[2]:
        last = u.get("last_bonus", "")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
            except:
                last_dt = datetime.min
        else:
            last_dt = datetime.min
        if datetime.utcnow() - last_dt < timedelta(hours=24):
            remaining = timedelta(hours=24) - (datetime.utcnow() - last_dt)
            hours = remaining.seconds // 3600
            await message.answer(texts["bonus_wait"].format(hours=hours))
            return
        bonus_amt = random.randint(500, 3000) + (1000 if u.get("premium") else 0)
        add_balance(uid, bonus_amt)
        update_user_field(uid, "last_bonus", datetime.utcnow().isoformat())
        await message.answer(texts["bonus_taken"].format(amt=bonus_amt), reply_markup=main_menu_kb(lang))
        return

    # Referral
    if text == menu[3]:
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"
        await message.answer(f"👥 Referral link:\n{link}\nReward: 5% of first deposit (simulated).")
        return

    # Withdraw
    if text == menu[4]:
        settings = load_settings()
        min_w = settings.get("min_withdraw", 1500)
        if u["balance"] < min_w:
            await message.answer(texts["no_money_game"].format(min=min_w))
            return
        # ask amount
        update_user_field(uid, "awaiting_withdraw", 1)
        await message.answer(f"💸 Enter amount to withdraw (min {min_w}):")
        return

    # Stats
    if text == menu[5]:
        cur.execute("SELECT COUNT(*), SUM(balance) FROM users")
        total_users, total_balance = cur.fetchone()
        await message.answer(f"📊 Users: {total_users}\nTotal balance: {total_balance}")
        return

    # Admin
    if text == menu[6]:
        if uid != ADMIN_ID:
            await message.answer("⛔ Admin area")
            return
        # admin menu
        kb = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton("/users"), KeyboardButton("/withdraws")],
            [KeyboardButton("/setmin"), KeyboardButton("/broadcast")],
            [KeyboardButton("/addfund")]
        ], resize_keyboard=True)
        await message.answer("⚙️ Admin commands (use text commands):", reply_markup=kb)
        return

    # Back button
    if text == "⬅️ Back":
        await message.answer("🏠 Main menu", reply_markup=main_menu_kb(lang))
        return

    # --- Mini-games handlers by text ---
    if text == "🔢 Number (1-5)":
        # check balance
        if u["balance"] < 1500:
            await message.answer(texts["no_money_game"].format(min=1500))
            return
        # present inline numbers
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=str(i), callback_data=f"num_{i}") for i in range(1,6)]
        ])
        await message.answer("Pick a number 1-5:", reply_markup=kb)
        return

    if text == "🎰 Slot":
        if u["balance"] < 1500:
            await message.answer(texts["no_money_game"].format(min=1500))
            return
        # play slot immediately
        if u["balance"] >= 1500:
            change_balance(uid, -1500)
        symbols = ["🍒","🍋","🍊","💎","7️⃣"]
        res = [random.choice(symbols) for _ in range(3)]
        if res[0]==res[1]==res[2]:
            win = 10000
            add_balance(uid, win)
            add_xp(uid, 10)
            await message.answer(f"🎰 {' '.join(res)}\n🎉 JACKPOT! +{win} so'm")
        else:
            await message.answer(f"🎰 {' '.join(res)}\n❌ Not matched. -1500 so'm")
        return

    if text == "🧠 Quiz":
        if u["balance"] < 1500:
            await message.answer(texts["no_money_game"].format(min=1500))
            return
        # choose question
        qbank = [("5+3?","8"),("Uzbek capital?","toshkent"),("2*6?","12"),("10-4?","6")]
        q,a = random.choice(qbank)
        update_user_field(uid, "current_quiz", a.lower())
        await message.answer(f"🧩 Question: {q}\nWrite answer within 60s.")
        # schedule auto-clear in 60s
        async def clear_quiz(u_id):
            await asyncio.sleep(60)
            cu = get_user(u_id)
            if cu and cu.get("current_quiz"):
                update_user_field(u_id, "current_quiz", "")
        asyncio.create_task(clear_quiz(uid))
        return

    if text == "🎡 Spin Wheel":
        # small wheel with prizes
        if u["balance"] < 1500:
            await message.answer(texts["no_money_game"].format(min=1500))
            return
        change_balance(uid, -1500)
        prizes = [0,1000,2000,5000,10000]
        prize = random.choice(prizes)
        if prize>0:
            add_balance(uid, prize)
            await message.answer(f"🎡 You won {prize} so'm!")
        else:
            await message.answer("🎡 No prize this time.")
        return

    if text == "⬅️ Asosiy":
        await message.answer("🏠 Main", reply_markup=main_menu_kb(lang))
        return

    # --- Admin quick commands fallback ---
    if text.startswith("/"):
        # handle admin commands
        if uid != ADMIN_ID:
            await message.answer("⛔ Not admin")
            return
        parts = text.split(maxsplit=2)
        cmd = parts[0].lower()
        if cmd == "/users":
            cur.execute("SELECT COUNT(*) FROM users")
            cnt = cur.fetchone()[0]
            await message.answer(f"Users: {cnt}")
            return
        if cmd == "/withdraws":
            cur.execute("SELECT id, user_id, amount, status FROM withdraws ORDER BY id DESC LIMIT 20")
            rows = cur.fetchall()
            if not rows:
                await message.answer("No withdraws")
                return
            s = "\n".join([f"{r[0]}: user={r[1]} amt={r[2]} status={r[3]}" for r in rows])
            await message.answer(s)
            return
        if cmd == "/setmin":
            # usage: /setmin 5000
            if len(parts)<2:
                await message.answer("Usage: /setmin 5000")
                return
            try:
                val = int(parts[1])
                save_settings({"min_withdraw": val})
                await message.answer(f"min_withdraw set to {val}")
            except:
                await message.answer("Invalid value")
            return
        if cmd == "/addfund":
            # /addfund <user> <amt>
            if len(parts)<3:
                await message.answer("Usage: /addfund user_id amount")
                return
            try:
                uid2 = int(parts[1])
                amt = int(parts[2])
                add_balance(uid2, amt)
                await message.answer("Added")
            except Exception as e:
                await message.answer("Error")
            return
        if cmd == "/broadcast":
            if len(parts)<2:
                await message.answer("Usage: /broadcast message")
                return
            msg = parts[1]
            cur.execute("SELECT user_id FROM users")
            for (urow,) in cur.fetchall():
                try:
                    asyncio.create_task(bot.send_message(urow, f"📣 Admin: {msg}"))
                except:
                    pass
            await message.answer("Broadcast started")
            return

    # --- Fallback: check user states like awaiting_withdraw or quiz answer ---
    # withdraw awaiting
    if u.get("awaiting_withdraw"):
        try:
            amt = int(text.replace(",",""))
        except:
            await message.answer("Enter numeric amount.")
            return
        settings = load_settings()
        min_w = settings.get("min_withdraw", 1500)
        if amt < min_w or amt > u["balance"]:
            await message.answer("Invalid amount or insufficient balance.")
            return
        # create withdraw request
        cur.execute("INSERT INTO withdraws(user_id, amount, created_at) VALUES(?,?,?)", (uid, amt, now_iso()))
        conn.commit()
        update_user_field(uid, "awaiting_withdraw", 0)
        await message.answer(TEXT[lang]["withdraw_sent"])
        # notify admin
        try:
            await bot.send_message(ADMIN_ID, TEXT[lang]["withdraw_notify_admin"].format(uid=uid, amt=amt))
        except:
            pass
        return

    # quiz answer
    if u.get("current_quiz"):
        correct = u.get("current_quiz","").lower()
        update_user_field(uid, "current_quiz", "")
        if text.lower()==correct:
            add_balance(uid, 10000)
            add_xp(uid, 15)
            await message.answer("🎉 Correct! +10 000 so'm and +15 XP")
        else:
            change_balance(uid, -1500)
            await message.answer(f"❌ Wrong. Correct: {correct}. -1500 so'm")
        return

    # else unknown
    await message.answer("❓ Unknown command or use menu.", reply_markup=main_menu_kb(lang))

# --- Inline callbacks (numbers game) ---
@dp.callback_query(F.data.startswith("num_") | F.data.startswith("choose_") | F.data.startswith("basic_"))
async def num_game_cb(call: types.CallbackQuery):
    data = call.data
    uid = call.from_user.id
    u = get_user(uid)
    # number games: callback like num_3 or basic_3
    try:
        chosen = int(data.split("_")[1])
    except:
        await call.answer()
        return
    if u["balance"] < 1500:
        await call.message.answer("❌ Insufficient balance")
        return await call.answer()
    secret = random.randint(1,5)
    if chosen == secret:
        add_balance(uid, 10000)
        add_xp(uid, 10)
        await call.message.answer(f"🎉 Win! Number {secret}. +10000 so'm")
    else:
        change_balance(uid, -1500)
        await call.message.answer(f"😢 Lose! Number was {secret}. -1500 so'm")
    await call.answer()

# --- Invest handling (demo using background tasks) ---
INVEST_PLANS = {
    "small": (1000, 10, 60),
    "medium": (5000, 15, 180),
    "large": (10000, 25, 300)
}

async def invest_finish_task(invest_id, user_id, amount, percent, finish_at):
    # Wait until finish_at (datetime string ISO)
    dt = datetime.fromisoformat(finish_at)
    now = datetime.utcnow()
    delay = (dt - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    # finalize
    profit = amount * percent // 100
    add_balance(user_id, amount + profit)
    cur.execute("UPDATE invests SET status='done' WHERE id=?", (invest_id,))
    conn.commit()
    try:
        await bot.send_message(user_id, f"💰 Invest finished: +{profit} so'm profit")
    except:
        pass

@dp.message(F.text == "🏦 Invest")
async def invest_menu(message: types.Message):
    uid = message.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Small (1000,10%)", callback_data="inv_small")],
        [InlineKeyboardButton(text="📈 Medium (5000,15%)", callback_data="inv_medium")],
        [InlineKeyboardButton(text="🏦 Large (10000,25%)", callback_data="inv_large")]
    ])
    await message.answer("Choose invest plan (demo durations):", reply_markup=kb)

@dp.callback_query(F.data.startswith("inv_"))
async def inv_cb(call: types.CallbackQuery):
    plan = call.data.split("_")[1]
    if plan not in INVEST_PLANS:
        await call.answer("Invalid")
        return
    amt, pct, dur = INVEST_PLANS[plan]
    uid = call.from_user.id
    u = get_user(uid)
    if u["balance"] < amt:
        await call.message.answer("❌ Not enough balance")
        return await call.answer()
    change_balance(uid, -amt)
    finish_at = (datetime.utcnow() + timedelta(seconds=dur)).isoformat()
    cur.execute("INSERT INTO invests(user_id, amount, percent, finish_at) VALUES(?,?,?,?)", (uid, amt, pct, finish_at))
    conn.commit()
    inv_id = cur.lastrowid
    asyncio.create_t
