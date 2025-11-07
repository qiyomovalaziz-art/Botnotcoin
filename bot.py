# bot.py
import os
import json
import asyncio
from typing import List, Dict, Any, Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

DATA_FILE = "data.json"
BOT_TOKEN = ("8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM")  # yoki to'g'ridan-to'g'ri yozing (xavfsizlik uchun env tavsiya)
ADMIN_ID = 7973934849

if BOT_TOKEN is None or ADMIN_ID == 0:
    raise SystemExit("Iltimos, TG_BOT_TOKEN va ADMIN_ID muhit o'zgaruvchilarini sozlang.")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# --- Yengil JSON saqlovchi ---
def load_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return {"required_channels": [], "orders": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(d: Dict[str, Any]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

data = load_data()

# --- FSM for ordering ---
class OrderStates(StatesGroup):
    waiting_name = State()
    waiting_service = State()
    waiting_amount = State()
    waiting_confirm = State()

# --- Helpers ---
def admin_only(func):
    async def wrapper(event, *a, **kw):
        user_id = (event.from_user.id if isinstance(event, Message) else event.from_user.id)
        if user_id != ADMIN_ID:
            if isinstance(event, Message):
                await event.reply("Siz bu komandani ishlata olmaysiz.")
            else:
                await event.message.answer("Siz bu komandani ishlata olmaysiz.")
            return
        return await func(event, *a, **kw)
    return wrapper

def make_start_kbd() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("🔎 Obunani tekshirish", callback_data="check_subs"))
    kb.add(InlineKeyboardButton("🛒 Buyurtma berish", callback_data="order"))
    kb.add(InlineKeyboardButton("📸 Instagram", url="https://instagram.com/your_instagram_here"))
    return kb

# --- Commands ---
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    d = load_data()
    channels: List[str] = d.get("required_channels", [])
    if channels:
        text = "Botga xush kelibsiz!\nQuyidagi kanallarga obuna bo'lishingiz kerak:"
        for ch in channels:
            text += f"\n• {ch}"
    else:
        text = "Botga xush kelibsiz!\nHozircha majburiy kanallar belgilanmagan."
    await message.answer(text, reply_markup=make_start_kbd())

# --- Admin: add channel ---
@dp.message(Command(commands=["add_channel"]))
@admin_only
async def cmd_add_channel(message: Message):
    await message.reply("Kanal username yoki invite linkini yuboring (masalan: @kanal yoki https://t.me/joinchat/...).\nYuborganingizdan so'ng men uni majburiylar ro'yxatiga qo'shaman.")
    # next message will be processed by simple handler below with a special prefix check
    # We'll mark by expecting next message to be a channel add — simplified approach:
    await message.bot.set_my_commands([])  # noop to avoid warnings

@dp.message()
async def catch_admin_channel_add(message: Message):
    # only admin messages here will act as channel additions if they start with @ or https
    if message.from_user.id != ADMIN_ID:
        # Not admin — maybe user is ordering; let FSM handle
        return
    text = message.text.strip()
    if text.startswith("@") or text.startswith("http"):
        d = load_data()
        channels = d.get("required_channels", [])
        if text in channels:
            await message.reply("Bu kanal allaqachon ro'yxatda.")
            return
        channels.append(text)
        d["required_channels"] = channels
        save_data(d)
        await message.reply(f"Kanal qo'shildi: {text}")
    # else: ignore (could be normal admin message)

@dp.message(Command(commands=["remove_channel"]))
@admin_only
async def cmd_remove_channel(message: Message):
    d = load_data()
    channels = d.get("required_channels", [])
    if not channels:
        await message.reply("Hech qanday majburiy kanal mavjud emas.")
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for ch in channels:
        kb.add(InlineKeyboardButton(ch, callback_data=f"rmch|{ch}"))
    await message.reply("O'chirmoqchi bo'lgan kanalni tanlang:", reply_markup=kb)

@dp.callback_query(lambda c: c.data and c.data.startswith("rmch|"))
@admin_only
async def cb_remove_channel(query: CallbackQuery):
    _, ch = query.data.split("|", 1)
    d = load_data()
    channels = d.get("required_channels", [])
    if ch in channels:
        channels.remove(ch)
        d["required_channels"] = channels
        save_data(d)
        await query.message.edit_text("Kanal o'chirildi.")
    else:
        await query.answer("Topilmadi.", show_alert=True)

@dp.message(Command(commands=["list_channels"]))
@admin_only
async def cmd_list_channels(message: Message):
    d = load_data()
    channels = d.get("required_channels", [])
    if not channels:
        await message.reply("Majburiy kanallar ro'yxati bo'sh.")
        return
    text = "Majburiy kanallar:\n" + "\n".join(f"• {c}" for c in channels)
    await message.reply(text)

# --- Subscription check ---
@dp.callback_query(lambda c: c.data == "check_subs")
async def cb_check_subs(query: CallbackQuery):
    user_id = query.from_user.id
    d = load_data()
    channels: List[str] = d.get("required_channels", [])
    if not channels:
        await query.message.answer("Majburiy kanallar belgilangan emas. Admin bilan bog'laning.")
        return
    not_joined = []
    for ch in channels:
        try:
            # If ch looks like @username, we can use it; if it's a join link, bot can't always check — notify admin.
            if ch.startswith("@"):
                chat = await bot.get_chat(ch)
                member = await bot.get_chat_member(chat.id, user_id)
                status = member.status  # 'member', 'creator', 'administrator', etc.
                if status in ("left", "kicked"):
                    not_joined.append(ch)
            else:
                # invite link or weird format — we can't reliably check via username,
                # so we consider it unchecked and instruct user to join manually.
                not_joined.append(ch + " (invite-link — qo'shiling va keyin tekshiring)")
        except Exception as e:
            # Agar bot kanalga admin emas yoki username noto'g'ri bo'lsa
            not_joined.append(f"{ch} (tekshirishda xato)")
    if not not_joined:
        await query.message.answer("Siz barcha majburiy kanallarga obuna ekansiz ✅")
    else:
        text = "Iltimos quyidagi kanallarga obuna bo'ling yoki adminga murojaat qiling:\n" + "\n".join(f"• {c}" for c in not_joined)
        await query.message.answer(text)

# --- Ordering flow ---
@dp.callback_query(lambda c: c.data == "order")
async def cb_order_start(query: CallbackQuery):
    await query.message.answer("Buyurtma berish: Ismingizni kiriting:")
    await dp.current_state(user=query.from_user.id).set_state(OrderStates.waiting_name)

@dp.message(OrderStates.waiting_name)
async def state_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Xizmat nomini kiriting (masalan: Instagram follower):")
    await state.set_state(OrderStates.waiting_service)

@dp.message(OrderStates.waiting_service)
async def state_service(message: Message, state: FSMContext):
    await state.update_data(service=message.text.strip())
    await message.answer("Miqdorni kiriting (raqam bilan):")
    await state.set_state(OrderStates.waiting_amount)

@dp.message(OrderStates.waiting_amount)
async def state_amount(message: Message, state: FSMContext):
    txt = message.text.strip()
    if not txt.isdigit():
        await message.answer("Iltimos faqat raqam kiriting.")
        return
    await state.update_data(amount=int(txt))
    data_st = await state.get_data()
    summary = (
        f"Buyurtma xulosasi:\n"
        f"Ism: {data_st['name']}\n"
        f"Xizmat: {data_st['service']}\n"
        f"Miqdor: {data_st['amount']}\n\n"
        "Tasdiqlaysizmi?"
    )
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="order_confirm"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="order_cancel"),
    )
    await message.answer(summary, reply_markup=kb)
    await state.set_state(OrderStates.waiting_confirm)

@dp.callback_query(lambda c: c.data == "order_confirm")
async def cb_order_confirm(query: CallbackQuery):
    state = dp.current_state(user=query.from_user.id)
    d = await state.get_data()
    store = load_data()
    order = {
        "user_id": query.from_user.id,
        "user_name": query.from_user.username or query.from_user.full_name,
        "name": d.get("name"),
        "service": d.get("service"),
        "amount": d.get("amount"),
        "status": "new"
    }
    store.setdefault("orders", []).append(order)
    save_data(store)
    await state.clear()
    await query.message.answer("Buyurtmangiz qabul qilindi. Admin bilan bog'laning yoki to'lovni amalga oshiring.")
    # notify admin
    try:
        await bot.send_message(ADMIN_ID, f"Yangi buyurtma:\n{order}")
    except Exception:
        pass

@dp.callback_query(lambda c: c.data == "order_cancel")
async def cb_order_cancel(query: CallbackQuery):
    await dp.current_state(user=query.from_user.id).clear()
    await query.message.answer("Buyurtma bekor qilindi.")

# --- Admin: view orders ---
@dp.message(Command(commands=["orders"]))
@admin_only
async def cmd_orders(message: Message):
    d = load_data()
    orders = d.get("orders", [])
    if not orders:
        await message.reply("Buyurtmalar yo'q.")
        return
    for o in orders[-20:]:
        await message.reply(json.dumps(o, ensure_ascii=False, indent=2))

# --- Fallback handler for plain text from users (non-admin) ---
@dp.message()
async def default_msg(message: Message):
    # If user writes something unexpected, show start keyboard
    await message.reply("Bot asosiy menyu:", reply_markup=make_start_kbd())

# --- Run ---
if __name__ == "__main__":
    print("Bot ishga tushmoqda...")
    try:
        dp.run_polling(bot)
    finally:
        save_data(load_data())
