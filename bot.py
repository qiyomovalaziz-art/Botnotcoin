# bot_all.py
import asyncio
import json
import os
import time
from typing import Dict, Any, Optional, List

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== CONFIG ==========
BOT_TOKEN = "8295341226:AAGfbow1rcM6gAJSO-2XnlTKN0Dk0brg4AE"   # <-- o'zgartiring
ADMIN_ID = 7973934849           # <-- o'zgartiring (Sizning Telegram ID)
ADMIN_PASS = "1234"            # oddiy admin parol (xohlasangiz o'zgartiring)
DATA_DIR = "data"
# ========== END CONFIG ==========

# Ensure data dir
os.makedirs(DATA_DIR, exist_ok=True)

# JSON fayl nomlari
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
SERVICES_FILE = os.path.join(DATA_DIR, "services.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
DEPOSITS_FILE = os.path.join(DATA_DIR, "deposits.json")
WITHDRAWS_FILE = os.path.join(DATA_DIR, "withdraws.json")

# init files if not exist
for f, default in [
    (CHANNELS_FILE, []),
    (SETTINGS_FILE, {"api_url": "", "api_key": "", "percent": 10}),
    (SERVICES_FILE, []),
    (USERS_FILE, {}),
    (ORDERS_FILE, {}),
    (DEPOSITS_FILE, {}),
    (WITHDRAWS_FILE, {})
]:
    if not os.path.exists(f):
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(default, fh, ensure_ascii=False, indent=2)

# Helper read/write
def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Bot init
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# --- Utility functions for persistent storage ---

def get_channels() -> List[str]:
    return read_json(CHANNELS_FILE)

def add_channel(username: str):
    ch = get_channels()
    if username not in ch:
        ch.append(username)
        write_json(CHANNELS_FILE, ch)

def remove_channel(username: str):
    ch = get_channels()
    if username in ch:
        ch.remove(username)
        write_json(CHANNELS_FILE, ch)

def get_settings() -> Dict[str, Any]:
    return read_json(SETTINGS_FILE)

def save_settings(d: Dict[str, Any]):
    write_json(SETTINGS_FILE, d)

def get_services() -> List[Dict[str, Any]]:
    return read_json(SERVICES_FILE)

def save_services(svcs: List[Dict[str, Any]]):
    write_json(SERVICES_FILE, svcs)

def get_users() -> Dict[str, Any]:
    return read_json(USERS_FILE)

def save_users(u: Dict[str, Any]):
    write_json(USERS_FILE, u)

def get_orders() -> Dict[str, Any]:
    return read_json(ORDERS_FILE)

def save_orders(o: Dict[str, Any]):
    write_json(ORDERS_FILE, o)

def get_deposits() -> Dict[str, Any]:
    return read_json(DEPOSITS_FILE)

def save_deposits(d: Dict[str, Any]):
    write_json(DEPOSITS_FILE, d)

def get_withdraws() -> Dict[str, Any]:
    return read_json(WITHDRAWS_FILE)

def save_withdraws(w: Dict[str, Any]):
    write_json(WITHDRAWS_FILE, w)

# --- Sub check ---
async def check_subs(user_id: int) -> bool:
    channels = get_channels()
    if not channels:
        return True  # agar kanal belgilanmagan bo'lsa, chek o'tkazilmasin
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            # kanalga bot admin bo'lmasa yoki xato bo'lsa - tekshirishni o'tkazib yubor
            return False
    return True

# --- User balance helpers ---
def get_balance(user_id: int) -> float:
    users = get_users()
    uid = str(user_id)
    return float(users.get(uid, {}).get("balance", 0.0))

def add_balance(user_id: int, amount: float):
    users = get_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"balance": 0.0, "ref": None}
    users[uid]["balance"] = float(users[uid].get("balance", 0.0)) + float(amount)
    save_users(users)

def sub_balance(user_id: int, amount: float) -> bool:
    users = get_users()
    uid = str(user_id)
    bal = float(users.get(uid, {}).get("balance", 0.0))
    if bal >= amount:
        users[uid]["balance"] = bal - amount
        save_users(users)
        return True
    return False

# --- API interaction for services & orders (SMM panel) ---
async def fetch_services_from_api():
    settings = get_settings()
    api_url = settings.get("api_url", "").rstrip("/")
    api_key = settings.get("api_key", "")
    if not api_url or not api_key:
        return {"error": "API sozlanmagan."}
    url = f"{api_url}/services"  # umumiy forma; APIingiz boshqacha bo'lsa admin paneldan o'zgartiring logikani
    headers = {"Authorization": api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                data = await resp.json()
                # kutilyotgan format: list of services [{id, name, rate, min, max, category}, ...]
                save_services(data)
                return {"ok": True, "count": len(data)}
    except Exception as e:
        return {"error": str(e)}

async def create_order_api(service_id: int, link: str, quantity: int) -> Dict[str, Any]:
    settings = get_settings()
    api_url = settings.get("api_url", "").rstrip("/")
    api_key = settings.get("api_key", "")
    if not api_url or not api_key:
        return {"error": "API sozlanmagan."}
    url = f"{api_url}/order"
    payload = {"service": service_id, "link": link, "quantity": quantity}
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=20) as resp:
                return await resp.json()
    except Exception as e:
        return {"error": str(e)}

async def get_order_status_api(order_id: int) -> Dict[str, Any]:
    settings = get_settings()
    api_url = settings.get("api_url", "").rstrip("/")
    api_key = settings.get("api_key", "")
    if not api_url or not api_key:
        return {"error": "API sozlanmagan."}
    url = f"{api_url}/order/{order_id}"
    headers = {"Authorization": api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                return await resp.json()
    except Exception as e:
        return {"error": str(e)}

# --- ID generator for orders / deposits / withdraws ---
def gen_id(prefix="ORD"):
    return f"{prefix}{int(time.time()*1000)}"

# ========== BOT HANDLERS ==========

# /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    if not await check_subs(message.from_user.id):
        kb = InlineKeyboardBuilder()
        for ch in get_channels():
            ch_clean = ch.replace("@", "")
            kb.button(text=f"🔗 {ch}", url=f"https://t.me/{ch_clean}")
        kb.button(text="✅ Obuna bo‘ldim", callback_data="check_subs")
        await message.answer("Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:", reply_markup=kb.as_markup())
        return

    kb = InlineKeyboardBuilder()
    kb.button(text="📦 Buyurtma berish", callback_data="menu_order")
    kb.button(text="🎮 Oʻyinlar (tez orada)", callback_data="menu_games")
    kb.button(text="💰 Hisobni toʻldirish", callback_data="menu_deposit")
    kb.button(text="🏧 Pul yechish", callback_data="menu_withdraw")
    kb.button(text="🧑‍💻 Admin panel", callback_data="menu_admin")
    await message.answer(f"Xush kelibsiz, {message.from_user.first_name}!", reply_markup=kb.as_markup())

# check subscription callback
@dp.callback_query(lambda c: c.data == "check_subs")
async def cb_check_subs(cq: CallbackQuery):
    if await check_subs(cq.from_user.id):
        await cq.message.edit_text("✅ Obuna tekshirildi. Endi davom etishingiz mumkin.")
        # show menu
        await cmd_start(cq.message)
    else:
        await cq.answer("Hamma kanallarga obuna bo‘lmagansiz.", show_alert=True)

# --- MENU: ORDER ---
@dp.callback_query(lambda c: c.data == "menu_order")
async def cb_menu_order(cq: CallbackQuery):
    settings = get_settings()
    if not settings.get("api_url") or not settings.get("api_key"):
        await cq.message.answer("⚠️ Xizmatlar API sozlanmagan. Admin bilan murojaat qiling.")
        return
    # yuklab olish
    svc_list = get_services()
    if not svc_list:
        res = await fetch_services_from_api()
        if res.get("error"):
            await cq.message.answer(f"Xizmatlarni yuklashda xato: {res['error']}")
            return
        svc_list = get_services()

    # kategoriyaga ajratib birinchi 20 xizmat ko'rsatamiz (soddaligi uchun)
    kb = InlineKeyboardBuilder()
    for svc in svc_list[:30]:
        # tugma data: svc_{id}
        kb.button(text=f"{svc.get('name')} — {svc.get('rate')}", callback_data=f"svc_{svc.get('id')}")
    kb.button(text="🔄 Yangilash", callback_data="refresh_services")
    kb.button(text="⬅️ Orqaga", callback_data="back_main")
    await cq.message.answer("Xizmatlardan birini tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(lambda c: c.data == "refresh_services")
async def cb_refresh_services(cq: CallbackQuery):
    await cq.message.answer("Xizmatlar yangilanmoqda...")
    res = await fetch_services_from_api()
    if res.get("error"):
        await cq.message.answer(f"Xato: {res['error']}")
    else:
        await cq.message.answer(f"✅ {res.get('count')} ta xizmat yuklandi.")
    # avtomatik qaytish
    await cb_menu_order(cq)

@dp.callback_query(lambda c: c.data and c.data.startswith("svc_"))
async def cb_select_service(cq: CallbackQuery):
    svc_id = int(cq.data.split("_", 1)[1])
    services = get_services()
    svc = next((s for s in services if int(s.get("id")) == svc_id), None)
    if not svc:
        await cq.message.answer("Xizmat topilmadi.")
        return
    # saqlash: foydalanuvchini qaysi xizmatni tanlaganini inline session sifatida saqlaymiz (oddiy faylga)
    users = get_users()
    uid = str(cq.from_user.id)
    if uid not in users:
        users[uid] = {"balance": 0.0, "session": {}}
    users[uid]["session"] = {"service_id": svc_id, "service_name": svc.get("name"), "rate": float(svc.get("rate",0))}
    save_users(users)

    # ko'rsatish va link/quantity so'rash
    await cq.message.answer(f"✅ Tanlandi: {svc.get('name')}\nIltimos, buyurtma uchun LINK yuboring (masalan: Instagram profili yoki post link):")
    # keyingi xabar handleriga o'tamiz - register
    @dp.message()
    async def receive_link(message: Message):
        if message.from_user.id != cq.from_user.id:
            return  # boshqa foydalanuvchilarga tegishli emas
        link = message.text.strip()
        users = get_users()
        session = users.get(str(message.from_user.id), {}).get("session")
        if not session:
            await message.answer("Seans yo'q. Iltimos xizmatni qaytadan tanlang.")
            return
        users[str(message.from_user.id)]["session"]["link"] = link
        save_users(users)
        await message.answer("Endi miqdorni yuboring (raqam bilan):")
        # register next for quantity
        @dp.message()
        async def receive_quantity(msg: Message):
            if msg.from_user.id != cq.from_user.id:
                return
            try:
                qty = int(msg.text.strip())
            except ValueError:
                await msg.answer("Iltimos faqat raqam kiriting.")
                return
            users = get_users()
            session = users.get(str(msg.from_user.id), {}).get("session")
            if not session:
                await msg.answer("Seans yo'q. Iltimos xizmatni qaytadan tanlang.")
                return
            service_rate = float(session.get("rate", 0.0))
            settings = get_settings()
            percent = float(settings.get("percent", 0.0))
            # umumiy narx = base_rate * qty * (1 + percent/100)
            total_price = service_rate * qty * (1 + percent/100.0)
            users[str(msg.from_user.id)]["session"]["qty"] = qty
            users[str(msg.from_user.id)]["session"]["total_price"] = round(total_price, 2)
            save_users(users)
            await msg.answer(f"Buyurtma:\nXizmat: {session.get('service_name')}\nLink: {session.get('link')}\nMiqdor: {qty}\nNarx (foiz bilan): {round(total_price,2)} so'm\n\n✅ Tasdiqlaysizmi?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data="confirm_order")],
                [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")]
            ]))
            # end receive_quantity
        # end receive_link
    # end cb_select_service


@dp.callback_query(lambda c: c.data == "cancel_order")
async def cb_cancel_order(cq: CallbackQuery):
    users = get_users()
    uid = str(cq.from_user.id)
    if uid in users and "session" in users[uid]:
        users[uid]["session"] = {}
        save_users(users)
    await cq.message.answer("Buyurtma bekor qilindi.")
    await cmd_start(cq.message)

@dp.callback_query(lambda c: c.data == "confirm_order")
async def cb_confirm_order(cq: CallbackQuery):
    users = get_users()
    uid = str(cq.from_user.id)
    session = users.get(uid, {}).get("session")
    if not session:
        await cq.message.answer("Seans tugagan. Iltimos yana tanlang.")
        return
    total_price = float(session.get("total_price", 0.0))
    # tekshirish: balans yetarlimi
    if get_balance(cq.from_user.id) < total_price:
        await cq.message.answer(f"Balans yetarli emas. Sizda: {get_balance(cq.from_user.id)} so'm, kerak: {total_price} so'm.")
        return
    # balansni yechamiz
    ok = sub_balance(cq.from_user.id, total_price)
    if not ok:
        await cq.message.answer("Balansdan yechilishda xatolik.")
        return
    # API ga buyurtma yuborish
    svc_id = session.get("service_id")
    link = session.get("link")
    qty = int(session.get("qty"))
    api_res = await create_order_api(svc_id, link, qty)
    # saqlash: orders.json
    orders = get_orders()
    order_id_local = gen_id("ORD")
    orders[order_id_local] = {
        "user_id": cq.from_user.id,
        "service_id": svc_id,
        "link": link,
        "quantity": qty,
        "total_price": total_price,
        "status": "created",
        "api_response": api_res,
        "created_at": int(time.time())
    }
    # agar API xato qaytarmasa va order_id qaytarsa saqlaymiz
    if isinstance(api_res, dict) and api_res.get("order"):
        orders[order_id_local]["api_order_id"] = api_res.get("order")
    save_orders(orders)
    # clear session
    users[uid]["session"] = {}
    save_users(users)
    await cq.message.answer(f"✅ Buyurtma qabul qilindi. Buyurtma ID: <code>{order_id_local}</code>\nAdmin tekshiradi va xizmat boshqaruv paneliga yuboriladi.\nBuyurtma holatini ko'rish uchun: /order {order_id_local}")
    # xabarnoma adminga
    await bot.send_message(ADMIN_ID, f"Yangi buyurtma: {order_id_local}\nFoydalanuvchi: {cq.from_user.full_name} ({cq.from_user.id})\nNarx: {total_price}")

# /order <id>
@dp.message(Command("order"))
async def cmd_order_info(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Foydalanish: /order <buyurtma_id>")
        return
    order_id = parts[1].strip()
    orders = get_orders()
    if order_id not in orders:
        await message.answer("Buyurtma topilmadi.")
        return
    ord = orders[order_id]
    text = f"Buyurtma: {order_id}\nXizmat: {ord.get('service_id')}\nLink: {ord.get('link')}\nMiqdor: {ord.get('quantity')}\nNarx: {ord.get('total_price')}\nStatus: {ord.get('status')}"
    await message.answer(text)

# --- DEPOSIT (Hisobni to'ldirish) ---
@dp.callback_query(lambda c: c.data == "menu_deposit")
async def cb_menu_deposit(cq: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 Bank orqali", callback_data="deposit_bank")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_main")]
    ])
    await cq.message.answer("Toʻldirish usulini tanlang:", reply_markup=kb)

@dp.callback_query(lambda c: c.data == "deposit_bank")
async def cb_deposit_bank(cq: CallbackQuery):
    # admin tomonidan sozlangan banklar va kartalar bo'lsa, ularni SETTINGS ga joylash mumkin.
    # Bu oddiy: foydalanuvchi qancha qo'yishini yozsin, keyin chek yukladi va admin tasdiqlaydi.
    await cq.message.answer("Iltimos toʻlov miqdorini kiriting (soʻm):")
    @dp.message()
    async def receive_amount(msg: Message):
        if msg.from_user.id != cq.from_user.id:
            return
        try:
            amount = float(msg.text.strip())
        except:
            await msg.answer("Iltimos raqam kiriting.")
            return
        # saqlaymiz depozit so'rovini vaqtincha
        dep_id = gen_id("DEP")
        deposits = get_deposits()
        deposits[dep_id] = {
            "user_id": msg.from_user.id,
            "amount": amount,
            "status": "pending",
            "created_at": int(time.time()),
            "proof": None
        }
        save_deposits(deposits)
        await msg.answer(f"Iltimos toʻlov chekini yuboring (rasm yoki skrin). Deposit ID: <code>{dep_id}</code>\nYakunlash uchun 'Toʻlov qildim' tugmasi bilan chek yuboring.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Toʻlov qildim (Yuborish)", callback_data=f"sent_deposit_{dep_id}")],
            [InlineKeyboardButton(text="Bekor qilish", callback_data=f"cancel_deposit_{dep_id}")]
        ]))

@dp.callback_query(lambda c: c.data and c.data.startswith("sent_deposit_"))
async def cb_sent_deposit(cq: CallbackQuery):
    dep_id = cq.data.split("_",2)[2]
    deposits = get_deposits()
    if dep_id not in deposits:
        await cq.message.answer("Deposit topilmadi.")
        return
    await cq.message.answer("Iltimos, chekni rasm yoki screenshot sifatida chatbotga yuboring (media):")
    @dp.message()
    async def receive_proof(msg: Message):
        if msg.from_user.id != cq.from_user.id:
            return
        if not msg.photo and not msg.document:
            await msg.answer("Iltimos rasm yuboring.")
            return
        # saqlash: telegram file_id ni depozitga joylaymiz
        file_id = None
        if msg.photo:
            file_id = msg.photo[-1].file_id
        elif msg.document:
            file_id = msg.document.file_id
        deposits = get_deposits()
        deposits[dep_id]["proof"] = file_id
        deposits[dep_id]["status"] = "sent"
        save_deposits(deposits)
        await msg.answer("✅ Chek yuborildi. Admin tekshiradi. Sizga xabar keladi.")
        # adminga xabar
        await bot.send_message(ADMIN_ID, f"Yangi deposit so'rovi: {dep_id}\nFoydalanuvchi: {msg.from_user.full_name} ({msg.from_user.id})\nSumma: {deposits[dep_id]['amount']}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"admin_dep_ok_{dep_id}"),
             InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin_dep_no_{dep_id}")]
        ]))

@dp.callback_query(lambda c: c.data and c.data.startswith("admin_dep_ok_"))
async def cb_admin_dep_ok(cq: CallbackQuery):
    dep_id = cq.data.split("_",3)[3] if len(cq.data.split("_"))>3 else cq.data.split("_",3)[2]
    deposits = get_deposits()
    if dep_id not in deposits:
        await cq.message.answer("Topilmadi.")
        return
    deposits[dep_id]["status"] = "approved"
    save_deposits(deposits)
    # balansni qo'shamiz
    add_balance(deposits[dep_id]["user_id"], float(deposits[dep_id]["amount"]))
    await cq.message.answer(f"Deposit {dep_id} tasdiqlandi va foydalanuvchi balansiga qoʻshildi.")
 
