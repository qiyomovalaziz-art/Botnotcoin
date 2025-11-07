#!/usr/bin/env python3
# bot.py
# Aiogram 3.x single-file bot: tasks, games, balance, payments, admin panel
# Replace TOKEN and ADMINS with your values

import asyncio
import logging
import sqlite3
from typing import Optional, List, Tuple
from pathlib import Path
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup,
    InlineKeyboardButton, InputFile
)

# ---------- CONFIG ----------
TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"
ADMINS = [7973934849]  # list of admin Telegram user IDs (integers)

DB_PATH = "bot_data.db"
REQUIRED_CHANNELS_TABLE = "required_channels"  # table name reference

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- DATABASE HELPERS ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0,
        ref INTEGER DEFAULT 0
    )
    """)
    # payments (toplash)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        status TEXT,
        receipt_file_id TEXT,
        bank_name TEXT
    )
    """)
    # withdraw requests
    cur.execute("""
    CREATE TABLE IF NOT EXISTS withdraws (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        card TEXT,
        status TEXT
    )
    """)
    # tasks (admin creates)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        link TEXT,
        reward REAL,
        media_file_id TEXT
    )
    """)
    # user tasks (submissions)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER,
        user_id INTEGER,
        proof_file_id TEXT,
        status TEXT
    )
    """)
    # banks (for deposit info)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS banks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        card TEXT
    )
    """)
    # services (placeholder for API services)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        api_url TEXT,
        api_key TEXT,
        percent REAL DEFAULT 0
    )
    """)
    # required channels (for mandatory subscription)
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS {REQUIRED_CHANNELS_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        title TEXT
    )
    """)
    # settings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    conn.commit()
    conn.close()

# ---------- UTIL ----------
def is_admin(user_id: int) -> bool:
    return user_id in ADMINS

def ensure_user(user_id: int, username: Optional[str]):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?,?)", (user_id, username))
    cur.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
    conn.commit()
    conn.close()

def get_user_balance(user_id: int) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return float(row["balance"]) if row else 0.0

def change_user_balance(user_id: int, delta: float):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (delta, user_id))
    conn.commit()
    conn.close()

# ---------- KEYBOARDS ----------
def main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📋 Buyurtma berish (Vazifa)", callback_data="menu_tasks")],
        [InlineKeyboardButton("🎮 O'yinlar", callback_data="menu_games")],
        [InlineKeyboardButton("💰 Hisobni to'ldirish", callback_data="menu_deposit")],
        [InlineKeyboardButton("💸 Pul yechish", callback_data="menu_withdraw")],
        [InlineKeyboardButton("⚙️ Profil / Balans", callback_data="menu_profile")],
    ])
    return kb

def admin_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📝 Vazifa qo'shish", callback_data="admin_add_task")],
        [InlineKeyboardButton("🏦 Bank qo'shish", callback_data="admin_add_bank")],
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔧 Majburiy kanallar", callback_data="admin_channels")],
        [InlineKeyboardButton("💳 To'lovlarni ko'rish", callback_data="admin_payments")],
        [InlineKeyboardButton("💵 Yechimlar", callback_data="admin_withdraws")],
    ])
    return kb

def games_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🏀 Basket (1x-6x)", callback_data="game_basket")],
        [InlineKeyboardButton("🎲 Qura tashlash", callback_data="game_lottery")],
        [InlineKeyboardButton("💣 Bomba (xavfli)", callback_data="game_bomb")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")],
    ])
    return kb

def deposit_banks_keyboard() -> InlineKeyboardMarkup:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM banks")
    rows = cur.fetchall()
    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(r["name"], callback_data=f"deposit_bank:{r['id']}")])
    if not buttons:
        buttons = [[InlineKeyboardButton("Admin hali bank qo'shmagan", callback_data="no_bank")]]
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ---------- BOT SETUP ----------
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------- START & HELP ----------
@dp.message(Command("start"))
async def cmd_start(msg: Message):
    ensure_user(msg.from_user.id, msg.from_user.username)
    # Check required channels and ask user to subscribe (we won't auto-verify, admin must check proof)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT chat_id, title FROM {REQUIRED_CHANNELS_TABLE}")
    rows = cur.fetchall()
    if rows:
        text = "Assalomu alaykum! Botga xush kelibsiz.\nIltimos, quyidagi kanallarga obuna bo'ling va tekshiruv uchun screenshot yuboring:\n\n"
        for r in rows:
            text += f"• {r['title']}\n"
        text += "\nObuna bo'lib bo'lgach, /start ni qayta bosing yoki /profile orqali tasdiqlovchi fayl yuboring."
    else:
        text = "Assalomu alaykum! Botga xush kelibsiz."

    await msg.answer(text, reply_markup=main_keyboard())

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.reply("Siz admin emassiz.")
        return
    await msg.answer("Admin panel:", reply_markup=admin_keyboard())

# ---------- PROFILE ----------
@dp.callback_query(Text("menu_profile"))
async def cb_profile(cq: CallbackQuery):
    uid = cq.from_user.id
    ensure_user(uid, cq.from_user.username)
    bal = get_user_balance(uid)
    text = f"👤 @{cq.from_user.username or cq.from_user.first_name}\n💰 Hisob: {bal:.2f} so'm\n\nKerakli tugmalar:"
    await cq.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📊 Hisobni ko'rsatish", callback_data="profile_show")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")],
    ]))

@dp.callback_query(Text("profile_show"))
async def cb_profile_show(cq: CallbackQuery):
    uid = cq.from_user.id
    bal = get_user_balance(uid)
    await cq.answer(f"Sizning balansingiz: {bal:.2f} so'm", show_alert=True)

# ---------- MAIN NAV ----------
@dp.callback_query(Text("back_to_main"))
async def cb_back(cq: CallbackQuery):
    await cq.message.edit_text("Asosiy menyu:", reply_markup=main_keyboard())

# ---------- TASKS (Vazifalar) ----------
@dp.callback_query(Text("menu_tasks"))
async def cb_menu_tasks(cq: CallbackQuery):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, reward FROM tasks")
    rows = cur.fetchall()
    if not rows:
        await cq.message.edit_text("Hozircha vazifalar yo'q. Keyinroq qaytib keling.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")],
        ]))
        return
    kb = InlineKeyboardMarkup()
    for r in rows:
        kb.add(InlineKeyboardButton(f"{r['title']} — {r['reward']} so'm", callback_data=f"task_view:{r['id']}"))
    kb.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main"))
    await cq.message.edit_text("Mavcut vazifalar:", reply_markup=kb)

@dp.callback_query(Text(startswith="task_view:"))
async def cb_task_view(cq: CallbackQuery):
    task_id = int(cq.data.split(":")[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    t = cur.fetchone()
    if not t:
        await cq.answer("Vazifa topilmadi.", show_alert=True)
        return
    text = f"📝 {t['title']}\n\n{t['description']}\n\nMukofot: {t['reward']} so'm"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Vazifani bajarib proof yuborish", callback_data=f"task_do:{task_id}")],
        [InlineKeyboardButton("🔗 Linkga o'tish", url=t['link'] if t['link'] else "https://t.me")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="menu_tasks")],
    ])
    await cq.message.edit_text(text, reply_markup=kb)

@dp.callback_query(Text(startswith="task_do:"))
async def cb_task_do(cq: CallbackQuery):
    task_id = int(cq.data.split(":")[1])
    await cq.message.answer("Vazifani bajarib, proof (rasm yoki video) yuboring. Yuborilgan fayl adminga tasdiqlash uchun jo'natiladi.")
    # Save a pending row indicating awaiting proof: we create a user_tasks entry with status 'awaiting_proof' and null proof_file_id
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO user_tasks (task_id, user_id, status) VALUES (?,?,?)", (task_id, cq.from_user.id, "awaiting_proof"))
    conn.commit()
    await cq.answer("Iltimos, fayl yuboring...")

@dp.message(lambda message: message.photo or message.video or message.document)
async def handle_proof(msg: Message):
    # find latest awaiting_proof for this user
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM user_tasks WHERE user_id = ? AND status = ? ORDER BY id DESC LIMIT 1", (msg.from_user.id, "awaiting_proof"))
    row = cur.fetchone()
    if not row:
        await msg.reply("Sizda tasdiqlanishi kerak boʻlgan vazifa topilmadi. Avval vazifani tanlang.")
        return
    ut_id = row["id"]
    # get file_id
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.video:
        file_id = msg.video.file_id
    elif msg.document:
        file_id = msg.document.file_id
    cur.execute("UPDATE user_tasks SET proof_file_id = ?, status = ? WHERE id = ?", (file_id, "pending_review", ut_id))
    conn.commit()
    # forward proof to all admins with context buttons
    text = f"Yangi vazifa proof (user: @{msg.from_user.username or msg.from_user.id} | id: {ut_id})."
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_task_approve:{ut_id}")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data=f"admin_task_reject:{ut_id}")],
    ])
    for admin in ADMINS:
        try:
            # send as copy so admin can see
            await bot.send_message(admin, text)
            if file_id:
                # send photo/video/document depending on type
                if msg.photo:
                    await bot.send_photo(admin, file_id, reply_markup=kb)
                elif msg.video:
                    await bot.send_video(admin, file_id, reply_markup=kb)
                else:
                    await bot.send_document(admin, file_id, reply_markup=kb)
        except Exception as e:
            logger.exception("Failed to forward to admin: %s", e)
    await msg.reply("Proof yuborildi! Admin tasdiqlashini kuting.")

@dp.callback_query(Text(startswith="admin_task_approve:"))
async def cb_admin_task_approve(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("Bu admin komandasi.", show_alert=True)
        return
    ut_id = int(cq.data.split(":")[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_tasks WHERE id = ?", (ut_id,))
    ut = cur.fetchone()
    if not ut:
        await cq.answer("Topilmadi.", show_alert=True)
        return
    # give reward
    cur.execute("SELECT reward FROM tasks WHERE id = ?", (ut["task_id"],))
    t = cur.fetchone()
    reward = float(t["reward"]) if t else 0.0
    cur.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (reward, ut["user_id"]))
    cur.execute("UPDATE user_tasks SET status = ? WHERE id = ?", ("approved", ut_id))
    conn.commit()
    conn.close()
    await cq.answer("Tasdiqlandi.", show_alert=True)
    try:
        await bot.send_message(ut["user_id"], f"🎉 Sizning vazifangiz tasdiqlandi! Hisobingizga {reward:.2f} so'm qo'shildi.")
    except Exception:
        pass
    await cq.message.edit_text("Vazifa tasdiqlandi.")

@dp.callback_query(Text(startswith="admin_task_reject:"))
async def cb_admin_task_reject(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("Bu admin komandasi.", show_alert=True)
        return
    ut_id = int(cq.data.split(":")[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_tasks WHERE id = ?", (ut_id,))
    ut = cur.fetchone()
    if not ut:
        await cq.answer("Topilmadi.", show_alert=True)
        return
    cur.execute("UPDATE user_tasks SET status = ? WHERE id = ?", ("rejected", ut_id))
    conn.commit()
    conn.close()
    await cq.answer("Bekor qilindi.", show_alert=True)
    try:
        await bot.send_message(ut["user_id"], "❌ Sizning vazifangiz bekor qilindi. Iltimos, qoidaga muvofiq qayta yuboring.")
    except Exception:
        pass
    await cq.message.edit_text("Vazifa rad etildi.")

# ---------- ADMIN: add task (simple flow using text) ----------
@dp.callback_query(Text("admin_add_task"))
async def cb_admin_add_task(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("Siz admin emassiz.", show_alert=True)
        return
    await cq.message.answer("Vazifa qo'shish: Iltimos quyidagi formatda yuboring:\nTitle|Description|link(optional)|reward\nMasalan:\nKanalga obuna bo'lib screenshot yuboring|Kanalga a'zo bo'ling va screenshot yuboring|https://t.me/example|200")
    await cq.answer()

@dp.message()
async def catch_admin_task_text(msg: Message):
    # Only handle if admin recently asked - simple approach: if admin and text contains '|'
    if not is_admin(msg.from_user.id):
        return
    text = msg.text or ""
    if "|" not in text:
        return
    parts = text.split("|")
    if len(parts) < 3:
        await msg.reply("Format noto'g'ri. Title|Description|link(optional)|reward")
        return
    title = parts[0].strip()
    description = parts[1].strip()
    link = parts[2].strip() if len(parts) >= 3 else ""
    reward = float(parts[3].strip()) if len(parts) >= 4 and parts[3].strip().replace('.','',1).isdigit() else 0.0
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, description, link, reward) VALUES (?,?,?,?)", (title, description, link, reward))
    conn.commit()
    conn.close()
    await msg.reply("Vazifa qo'shildi.")

# ---------- BANKS (for deposits) ----------
@dp.callback_query(Text("admin_add_bank"))
async def cb_admin_add_bank(cq: CallbackQuery):
    if not is_admin(cq.from_user.id):
        await cq.answer("Siz admin emassiz.", show_alert=True)
        return
    await cq.message.answer("Bank qo'shish: format: Bank nomi|karta raqami\nMasalan:\nXalq bank|8600************")
    await cq.answer()

@dp.message()
async def catch_admin_bank_text(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    text = msg.text or ""
    if "|" not in text:
        return
    name, card = [p.strip() for p in text.split("|", 1)]
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO banks (name, card) VALUES (?,?)", (name, card))
    conn.commit()
    conn.close()
    await msg.reply("Bank qo'shildi.")

# ---------- DEPOSIT FLOW ----------
@dp.callback_query(Text("menu_deposit"))
async def cb_menu_deposit(cq: CallbackQuery):
    await cq.message.edit_text("To'ldirish uchun bankni tanlang:", reply_markup=deposit_banks_keyboard())

@dp.callback_query(Text(startswith="deposit_bank:"))
async def cb_deposit_bank(cq: CallbackQuery):
    bank_id = int(cq.data.split(":")[1])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, card FROM banks WHERE id = ?", (bank_id,))
    b = cur.fetchone()
    if not b:
        await cq.answer("Bank topilmadi.", show_alert=True)
        return
    await cq.message.answer(f"To'lovni quyidagi karta raqamga amalga oshiring:\n\n{b['name']}\n{b['card']}\n\nTo'lov summasini kiriting (so'm):")
    # save temporary state into settings with user id key
    conn.close()
    # store a simple state file keyed by user id
    Path(f"state_deposit_{cq.from_user.id}.txt").write_text(str(bank_id))
    await cq.answer()

@dp.message()
async def catch_deposit_amount(msg: Message):
    # only if a deposit state file exists for this user
    state_file = Path(f"state_deposit_{msg.from_user.id}.txt")
    if not state_file.exists():
        return
    text = (msg.text or "").strip()
    if not text.replace('.', '', 1).isdigit():
        await msg.reply("Iltimos, raqam ko'rinishida miqdorni kiriting.")
        return
    amount = float(text)
    bank_id = int(state_file.read_text())
    state_file.unlink()
    # create payment record with status 'awaiting'
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM banks WHERE id = ?", (bank_id,))
    b = cur.fetchone()
    bank_name = b["name"] if b else "Noma'lum"
    cur.execute("INSERT INTO payments (user_id, amount, status, bank_name) VALUES (?,?,?,?)", (msg.from_user.id, amount, "awaiting", bank_name))
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    await msg.reply("To'lov uchun chek yoki skrin yuboring (rasm, document). Yuborganingizdan so'ng admin tasdiqlaydi.")
    # store payment id in temporary file for receipt association
    Path(f"state_payment_receipt_{msg.from_user.id}.txt").write_text(str(pid))

@dp.message(lambda message: message.photo or message.document)
async def catch_deposit_receipt(msg: Message):
    state_file = Path(f"state_payment_receipt_{msg.from_user.id}.txt")
    if not state_file.exists():
        return
    pid = int(state_file.read_text())
    state_file.unlink()
    file_id = None
    if msg.photo:
        file_id = msg.photo[-1].file_id
    elif msg.document:
        file_id = msg.document.file_id
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE payments SET receipt_file_id = ? WHERE id = ?", (file_id, pid))
    conn.commit()
    # notify admins
    cur.execute("SELECT user_id, amount, bank_name FROM payments WHERE id = ?", (pid,))
    p = cur.fetchone()
    conn.close()
    text = f"Yangi to'lov arizasi:\nUser: @{msg.from_user.username or msg.from_user.id}\nSumma: {p['amount']} so'm\nBank: {p['bank_name']}\nPayID: {pid
