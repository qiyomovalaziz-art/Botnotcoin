import asyncio
import json
import os
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

TOKEN = "8379130776:AAFP_ZIt1T2ds_p5vBILyFzvj8RaKeIDLRM"  # ← bu yerga tokeningizni yozing
ADMIN_ID = 7973934849

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(uid):
    data = load_data()
    if str(uid) not in data:
        data[str(uid)] = {
            "balance": 1000,
            "xp": 0,
            "level": 1,
            "bonus_time": "0",
            "invest": 0,
            "ref": 0,
            "games": 0,
            "wins": 0
        }
        save_data(data)
    return data[str(uid)]

def update_user(uid, key, value):
    data = load_data()
    data[str(uid)][key] = value
    save_data(data)

def main_menu():
    buttons = [
        [KeyboardButton(text="💰 Balans"), KeyboardButton(text="🎮 O‘yin")],
        [KeyboardButton(text="🏦 Invest"), KeyboardButton(text="🎁 Bonus")],
        [KeyboardButton(text="👥 Referal"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="⚙️ Admin panel")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
@dp.message(Command("start"))
async def start(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"👋 Salom, <b>{message.from_user.first_name}</b>!\n"
        f"Sizga 1000 so‘m bonus berildi 🎁\n\n"
        f"Darajangiz: {user['level']} | XP: {user['xp']}",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.message(F.text == "💰 Balans")
async def balance(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"💳 Balans: {user['balance']} so‘m\n"
        f"🏦 Invest: {user['invest']} so‘m\n"
        f"🎮 O‘yinlar: {user['games']}\n"
        f"⭐ XP: {user['xp']} | Level: {user['level']}"
    )

@dp.message(F.text == "🎮 O‘yin")
async def game_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"game_{i}") for i in range(1, 6)],
        [InlineKeyboardButton(text=str(i), callback_data=f"game_{i}") for i in range(6, 11)]
    ])
    await message.answer("🎯 1 dan 10 gacha son tanlang:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("game_"))
async def game_play(call: types.CallbackQuery):
    number = int(call.data.split("_")[1])
    rand = random.randint(1, 10)
    user = get_user(call.from_user.id)
    text = ""
    if number == rand:
        user["balance"] += 500
        user["xp"] += 10
        user["wins"] += 1
        text = f"🎉 To‘g‘ri topdingiz! +500 so‘m, +10 XP\nRaqam: {rand}"
    else:
        user["balance"] -= 200
        text = f"😢 Afsus, raqam {rand} edi. −200 so‘m"
    user["games"] += 1
    if user["xp"] >= user["level"] * 100:
        user["level"] += 1
        text += f"\n🏅 Tabriklaymiz! Siz {user['level']} darajaga chiqdingiz!"
    update_user(call.from_user.id, "balance", user["balance"])
    update_user(call.from_user.id, "xp", user["xp"])
    update_user(call.from_user.id, "level", user["level"])
    update_user(call.from_user.id, "games", user["games"])
    update_user(call.from_user.id, "wins", user["wins"])
    await call.message.answer(text)
    await call.answer()

@dp.message(F.text == "🎁 Bonus")
async def bonus(message: types.Message):
    user = get_user(message.from_user.id)
    now = datetime.now()
    if user["bonus_time"] != "0":
        last = datetime.fromisoformat(user["bonus_time"])
        if now - last < timedelta(hours=24):
            diff = timedelta(hours=24) - (now - last)
            return await message.answer(f"⏳ Bonusni {diff.seconds // 3600} soatdan keyin olasiz.")
    user["balance"] += 500
    user["bonus_time"] = now.isoformat()
    update_user(message.from_user.id, "balance", user["balance"])
    update_user(message.from_user.id, "bonus_time", user["bonus_time"])
    await message.answer("🎁 500 so‘m bonus qo‘shildi!")

@dp.message(F.text == "🏦 Invest")
async def invest(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Kichik (1000 so‘m, 10%)", callback_data="inv_1000_10")],
        [InlineKeyboardButton(text="📈 O‘rta (5000 so‘m, 15%)", callback_data="inv_5000_15")],
        [InlineKeyboardButton(text="🏦 Katta (10000 so‘m, 25%)", callback_data="inv_10000_25")]
    ])
    await message.answer("💸 Sarmoya turini tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith("inv_"))
async def invest_action(call: types.CallbackQuery):
    _, amount, percent = call.data.split("_")
    amount = int(amount)
    percent = int(percent)
    user = get_user(call.from_user.id)
    if user["balance"] < amount:
        return await call.message.answer("❌ Balansingizda mablag‘ yetarli emas.")
    user["balance"] -= amount
    user["invest"] += amount
    save_data(load_data())
    await call.message.answer(
        f"✅ {amount} so‘m sarmoya qilindi.\nFoyda {percent}% bo‘ladi. Kuting..."
    )
    await asyncio.sleep(60)
    profit = int(amount * percent / 100)
    user["balance"] += amount + profit
    user["invest"] -= amount
    update_user(call.from_user.id, "balance", user["balance"])
    update_user(call.from_user.id, "invest", user["invest"])
    await call.message.answer(f"💰 Sarmoya yakunlandi! Sizga {profit} so‘m foyda qo‘shildi.")
    await call.answer()

@dp.message(F.text == "📊 Statistika")
async def stats(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"📊 Sizning statistikangiz:\n\n"
        f"🎮 O‘yinlar: {user['games']} ta\n"
        f"🏆 Yutuqlar: {user['wins']} ta\n"
        f"💰 Balans: {user['balance']} so‘m\n"
        f"⭐ XP: {user['xp']} | Level: {user['level']}"
    )

@dp.message(F.text == "👥 Referal")
async def referal(message: types.Message):
    link = f"https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}"
    await message.answer(f"👥 Do‘stlaringizni taklif qiling va 5% bonus oling!\n\n🔗 Havola: {link}")

@dp.message(F.text == "⚙️ Admin panel")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Siz admin emassiz.")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton(text="📢 Hammaga xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💰 Statistika", callback_data="admin_stats")]
    ])
    await message.answer("⚙️ Admin panel:", reply_markup=kb)

@dp.callback_query(F.data == "admin_users")
async def admin_users(call: types.CallbackQuery):
    data = load_data()
    await call.message.answer(f"📋 Umumiy foydalanuvchilar: {len(data)} ta")
    await call.answer()

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: types.CallbackQuery):
    data = load_data()
    total_balance = sum([u["balance"] for u in data.values()])
    total_games = sum([u["games"] for u in data.values()])
    await call.message.answer(f"💰 Jami balanslar: {total_balance}\n🎮 O‘yinlar soni: {total_games}")
    await call.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: types.CallbackQuery):
    await call.message.answer("✍️ Hammaga yuboriladigan xabarni yozing:")
    @dp.message()
    async def broadcast_msg(msg: types.Message):
        data = load_data()
        for uid in data.keys():
            try:
                await bot.send_message(int(uid), msg.text)
            except:
                pass
        await msg.answer("✅ Xabar yuborildi.")
        dp.message.handlers.unregister(broadcast_msg)

async def main():
    print("🚀 Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
