#!/usr/bin/env python3
# bot.py — Aiogram 3.x Telegram bot
# Railway yoki local serverda ishlaydi

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery

# ================= CONFIG =================
TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"   # <-- Bu yerga bot tokeningni yoz
ADMINS = [7973934849]                # <-- O‘zingning Telegram ID ni yoz
DB_PATH = "bot_data.db"

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= DATABASE =================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        link TEXT,
        reward REAL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS user_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        user_id INTEGER,
        proof_file_id TEXT,
        status TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS banks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        card TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        status TEXT,
        bank_name TEXT,
        receipt_file_id TEXT
    )""")

    conn.commit()
    conn.close()

# ================= UTILS =================
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def ensure_user(user_id: int, username: Optional[str]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    cur.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
    conn.commit()
    conn.close()

def get_balance(uid: int) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE id = ?", (uid,))
    row = cur.fetchone()
    conn.close()
    return row["balance"] if row else 0.0

def add_balance(uid: int, amount: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, uid))
    conn.commit()
    conn.close()

# ================= KEYBOARDS =================
def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📋 Vazifalar", callback_data="menu_tasks")],
        [InlineKeyboardButton("💰 Hisobni to‘ldirish", callback_data="menu_deposit")],
        [InlineKeyboardButton("💸 Pul yechish", callback_data="menu_withdraw")],
        [InlineKeyboardButton("⚙️ Profil", callback_data="menu_profile")],
    ])

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("➕ Vazifa qo‘shish", callback_data="admin_add_task")],
        [InlineKeyboardButton("🏦 Bank qo‘shish", callback_data="admin_add_bank")],
        [InlineKeyboardButton("💳 To‘lovlarni ko‘rish", callback_data="admin_payments")],
    ])

# ================= BOT =================
bot = Bot(TOKEN)
dp = Dispatcher()

# ---------- START ----------
@dp.message(Command("start"))
async def start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    await msg.answer("👋 Assalomu alaykum! Xush kelibsiz.", reply_markup=main_kb())

# ---------- ADMIN PANEL ----------
@dp.message(Command("admin"))
async def admin_panel(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("Siz admin emassiz!")
        return
    await msg.answer("Admin panel:", reply_markup=admin_kb())

# ---------- PROFILE ----------
@dp.callback_query(Text("menu_profile"))
async def cb_profile(cq: CallbackQuery):
    bal = get_balance(cq.from_user.id)
    await cq.message.edit_text(f"👤 Profil\n💰 Balans: {bal:.2f} so‘m", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]
    ]))

@dp.callback_query(Text("back_main"))
async def cb_back_main(cq: CallbackQuery):
    await cq.message.edit_text("Asosiy menyu:", reply_markup=main_kb())

# ---------- ADMIN ADD TASK ----------
@dp.callback_query(Text("admin_add_task"))
async def cb_add_task(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return
    await cq.message.answer("Vazifa formati: sarlavha|tavsif|link|mukofot\n\nMasalan:\nObuna bo‘ling|Kanalga obuna bo‘ling|https://t.me/example|200")

@dp.message()
async def catch_admin_task(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    if "|" not in msg.text:
        return
    title, desc, link, reward = msg.text.split("|")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, description, link, reward) VALUES (?, ?, ?, ?)", (title.strip(), desc.strip(), link.strip(), float(reward)))
    conn.commit()
    conn.close()
    await msg.reply("✅ Vazifa qo‘shildi!")

# ---------- TASKS ----------
@dp.callback_query(Text("menu_tasks"))
async def cb_tasks(cq: CallbackQuery):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, reward FROM tasks")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        await cq.message.edit_text("Vazifalar hozircha yo‘q.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("🔙 Orqaga", callback_data="back_main")]]))
        return
    kb = InlineKeyboardMarkup()
    for r in rows:
        kb.add(InlineKeyboardButton(f"{r['title']} — {r['reward']} so‘m", callback_data=f"task:{r['id']}"))
    kb.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_main"))
    await cq.message.edit_text("📋 Vazifalar:", reply_markup=kb)

@dp.callback_query(Text(startswith="task:")))
async def cb_task(cq: CallbackQuery):
    tid = int(cq.data.split(":")[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (tid,))
    t = cur.fetchone()
    conn.close()
    if not t:
        await cq.answer("Topilmadi!", show_alert=True)
        return
    text = f"📝 {t['title']}\n{t['description']}\n💰 Mukofot: {t['reward']} so‘m"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔗 Link", url=t['link'])],
        [InlineKeyboardButton("✅ Proof yuborish", callback_data=f"proof:{tid}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="menu_tasks")]
    ])
    await cq.message.edit_text(text, reply_markup=kb)

# ---------- PROOF YUBORISH ----------
@dp.callback_query(Text(startswith="proof:")))
async def cb_proof(cq: CallbackQuery):
    tid = int(cq.data.split(":")[1])
    Path(f"proof_{cq.from_user.id}.txt").write_text(str(tid))
    await cq.message.answer("Vazifani bajargan rasmingizni yuboring 📸")

@dp.message(lambda msg: msg.photo)
async def proof_received(msg: Message):
    state = Path(f"proof_{msg.from_user.id}.txt")
    if not state.exists():
        return
    tid = int(state.read_text())
    file_id = msg.photo[-1].file_id
    state.unlink()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO user_tasks (task_id, user_id, proof_file_id, status) VALUES (?, ?, ?, ?)", (tid, msg.from_user.id, file_id, "pending"))
    conn.commit()
    conn.close()

    for admin in ADMINS:
        await bot.send_photo(admin, file_id, caption=f"Yangi proof: user={msg.from_user.id}, task={tid}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{msg.from_user.id}:{tid}")],
            [InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{msg.from_user.id}:{tid}")]
        ]))
    await msg.reply("Proof yuborildi! Admin tasdiqlashini kuting ✅")

# ---------- ADMIN TASDIQLASH ----------
@dp.callback_query(Text(startswith="approve:")))
async def cb_approve(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return
    _, uid, tid = cq.data.split(":")
    uid, tid = int(uid), int(tid)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT reward FROM tasks WHERE id = ?", (tid,))
    reward = cur.fetchone()["reward"]
    add_balance(uid, reward)
    cur.execute("UPDATE user_tasks SET status = ? WHERE task_id = ? AND user_id = ?", ("approved", tid, uid))
    conn.commit()
    conn.close()
    await cq.answer("Tasdiqlandi ✅", show_alert=True)
    await bot.send_message(uid, f"🎉 Vazifa tasdiqlandi! +{reward} so‘m hisobingizga qo‘shildi.")

@dp.callback_query(Text(startswith="reject:")))
async def cb_reject(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        return
    _, uid, tid = cq.data.split(":")
    uid, tid = int(uid), int(tid)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE user_tasks SET status = ? WHERE task_id = ? AND user_id = ?", ("rejected", tid, uid))
    conn.commit()
    conn.close()
    await cq.answer("Rad etildi ❌", show_alert=True)
    await bot.send_message(uid, "❌ Vazifangiz rad etildi. Qayta urinib ko‘ring.")

# ================= MAIN =================
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
