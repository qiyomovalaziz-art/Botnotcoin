import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from dotenv import load_dotenv

# .env dan tokenni olish
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======== Asosiy menyu tugmalari ========
def main_menu():
    kb = [
        [InlineKeyboardButton(text="💰 Hisobni to‘ldirish", callback_data="top_up")],
        [InlineKeyboardButton(text="📦 Buyurtma berish", callback_data="order")],
        [InlineKeyboardButton(text="🎮 O‘yinlar", callback_data="games")],
        [InlineKeyboardButton(text="💬 Adminga yozish", callback_data="admin_msg")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ======== /start ========
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Salom! Bu bot orqali balans to‘ldirish, o‘yin o‘ynash va topshiriqlar bajarish mumkin.",
        reply_markup=main_menu()
    )

# ======== Hisobni to‘ldirish ========
@dp.callback_query(Text("top_up"))
async def top_up_handler(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="Payme", callback_data="pay:Payme")],
        [InlineKeyboardButton(text="Click", callback_data="pay:Click")],
        [InlineKeyboardButton(text="UZUM", callback_data="pay:UZUM")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_main")]
    ]
    await callback.message.edit_text("💳 To‘lov tizimini tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(Text(startswith="pay:"))
async def process_payment(callback: CallbackQuery):
    pay_name = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"💸 {pay_name} orqali to‘lov qilish uchun:\n\n"
        f"Karta raqam: 8600 1234 5678 9999\n"
        f"Ism: BOT ADMIN\n\n"
        f"To‘lov qilganingizdan so‘ng 'To‘lov qildim' tugmasini bosing.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ To‘lov qildim", callback_data=f"proof:{pay_name}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="top_up")]
        ])
    )

@dp.callback_query(Text(startswith="proof:"))
async def proof_submit(callback: CallbackQuery):
    pay_name = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"📤 Iltimos, {pay_name} orqali to‘lov chekini yuboring (rasm shaklida)."
    )

# ======== Buyurtma berish ========
@dp.callback_query(Text("order"))
async def order_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📦 Buyurtma berish uchun admin tomonidan xizmatlar ulanadi.\nHozircha mavjud emas.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_main")]
        ])
    )

# ======== O‘yinlar menyusi ========
@dp.callback_query(Text("games"))
async def games_menu(callback: CallbackQuery):
    kb = [
        [InlineKeyboardButton(text="🏀 Basketbol", callback_data="game:basket")],
        [InlineKeyboardButton(text="🎲 Qura tashlash", callback_data="game:dice")],
        [InlineKeyboardButton(text="💣 Bombalar o‘yini", callback_data="game:bomb")],
        [InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="daily_bonus")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_main")]
    ]
    await callback.message.edit_text("🎮 O‘yin turini tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(Text(startswith="game:"))
async def play_game(callback: CallbackQuery):
    game_name = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"🎮 Siz {game_name} o‘yinini tanladingiz!\nO‘yin tizimi hali yo‘lga qo‘yilmagan.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="games")]
        ])
    )

# ======== Kunlik bonus ========
@dp.callback_query(Text("daily_bonus"))
async def daily_bonus(callback: CallbackQuery):
    await callback.message.edit_text("🎁 Sizga bugungi bonus: 100 so‘m qo‘shildi!")

# ======== Adminga yozish ========
@dp.callback_query(Text("admin_msg"))
async def admin_msg(callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 Adminga xabar yuborish uchun yozuv yuboring. (matn, rasm yoki video)",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_main")]
        ])
    )

# ======== Orqaga menyuga ========
@dp.callback_query(Text("back_main"))
async def back_main(callback: CallbackQuery):
    await callback.message.edit_text("🏠 Asosiy menyu:", reply_markup=main_menu())

# ======== Xabar yuborishlar uchun ========
@dp.message()
async def echo_all(message: Message):
    await message.answer("❗️Iltimos, tugmalardan foydalaning.")

# ======== Run ========
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
