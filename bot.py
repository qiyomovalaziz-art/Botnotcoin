import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ------------------- Sozlamalar -------------------
BOT_TOKEN = "BOT_TOKENINGNI_BU_YERGA_QO'Y"  # <-- Shu joyga token qo'y
ADMIN_ID = 123456789  # <-- O'zingning Telegram ID'ingni yoz
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ------------------- Boshlanish -------------------
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📢 Kanalga obuna bo'lish", url="https://t.me/yourchannel"),
        InlineKeyboardButton("✅ Tekshirish", callback_data="check_subs")
    )
    await msg.answer(
        f"Salom, {msg.from_user.first_name}! 👋\n"
        "Botdan foydalanish uchun avval kanalga obuna bo‘ling!",
        reply_markup=keyboard
    )

@dp.callback_query_handler(Text(equals="check_subs"))
async def check_subs(call: types.CallbackQuery):
    # Kanal obunasini tekshirish
    try:
        member = await bot.get_chat_member(chat_id="@yourchannel", user_id=call.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            menu = ReplyKeyboardMarkup(resize_keyboard=True)
            menu.add(KeyboardButton("🛒 Buyurtma berish"),
                     KeyboardButton("🎮 O‘yinlar"),
                     KeyboardButton("💰 Hisobni to‘ldirish"),
                     KeyboardButton("💬 Adminga yozish"))
            await call.message.answer("✅ Siz obuna bo‘lgansiz! Endi menyudan tanlang:", reply_markup=menu)
        else:
            await call.answer("Avval kanalga obuna bo‘ling!", show_alert=True)
    except Exception:
        await call.answer("Kanal topilmadi yoki bot admin emas!", show_alert=True)

# ------------------- Adminga yozish -------------------
@dp.message_handler(Text(equals="💬 Adminga yozish"))
async def contact_admin(msg: types.Message):
    await msg.answer("Adminga xabar yuborish uchun matn yuboring:")
    @dp.message_handler()
    async def forward_to_admin(message: types.Message):
        await bot.send_message(ADMIN_ID, f"📩 Yangi xabar @{message.from_user.username} dan:\n{message.text}")
        await message.answer("✅ Xabar adminga yuborildi!")

# ------------------- Hisob to‘ldirish -------------------
@dp.message_handler(Text(equals="💰 Hisobni to‘ldirish"))
async def deposit(msg: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("Payme", callback_data="bank_payme"),
        InlineKeyboardButton("Click", callback_data="bank_click"),
        InlineKeyboardButton("Apelsin", callback_data="bank_apelsin")
    )
    await msg.answer("💳 To‘lov tizimini tanlang:", reply_markup=kb)

@dp.callback_query_handler(Text(startswith="bank_"))
async def choose_bank(call: types.CallbackQuery):
    bank = call.data.split("_")[1]
    await call.message.answer(
        f"💳 Siz {bank.title()} ni tanladingiz.\n"
        "To‘lov uchun karta raqam: 8600 1234 5678 9000\n\n"
        "To‘lov qilingandan so‘ng **chekni yuboring.**"
    )

# ------------------- O‘yinlar menyusi -------------------
@dp.message_handler(Text(equals="🎮 O‘yinlar"))
async def games_menu(msg: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🏀 Basketbol", "🎲 Qura tashlash")
    kb.add("💣 Xavfli bomba", "🎳 Bowling")
    kb.add("🎁 Kunlik bonus", "🔙 Ortga")
    await msg.answer("🎮 O‘yin tanlang:", reply_markup=kb)

# ------------------- Oddiy o‘yin (random ball) -------------------
import random

@dp.message_handler(Text(equals="🏀 Basketbol"))
async def basket_game(msg: types.Message):
    res = random.choice(["200 so‘m yutding!", "300 so‘m yutding!", "Yutqazding 😢"])
    await msg.answer(f"🏀 Basketbol natijasi: {res}")

@dp.message_handler(Text(equals="🎲 Qura tashlash"))
async def dice_game(msg: types.Message):
    x = random.randint(1, 6)
    await msg.answer(f"🎲 Tashlangan son: {x}")

@dp.message_handler(Text(equals="💣 Xavfli bomba"))
async def bomb_game(msg: types.Message):
    x = random.randint(1, 5)
    if x == 3:
        await msg.answer("💣 Bomba portladi! Pul yo‘qoldi 😬")
    else:
        await msg.answer("🎉 Omadingiz keldi! Pul yutdingiz!")

@dp.message_handler(Text(equals="🎳 Bowling"))
async def bowling_game(msg: types.Message):
    await msg.answer("🎳 Bowling tashlandi! Natija: " + random.choice(["Strike!", "Miss!", "Half!"]))

# ------------------- Kunlik bonus -------------------
@dp.message_handler(Text(equals="🎁 Kunlik bonus"))
async def daily_bonus(msg: types.Message):
    bonus = random.randint(100, 500)
    await msg.answer(f"🎁 Sizga {bonus} so‘m bonus berildi!")

# ------------------- Botni ishga tushirish -------------------
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
