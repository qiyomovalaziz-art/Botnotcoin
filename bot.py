import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# 🔹 Token va admin ID
BOT_TOKEN = "BOT_TOKENINGNI_BU_YERGA_QO'Y"  # Token shu yerga
ADMIN_ID = 123456789  # Admin ID shu yerga

# 🔹 Log
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🔹 Start buyrug‘i
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url="https://t.me/yourchannel")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs")]
    ])
    await message.answer(
        f"Salom, {message.from_user.first_name}! 👋\n\n"
        f"Botdan foydalanish uchun avval kanalga obuna bo‘ling 👇",
        reply_markup=kb
    )

# 🔹 Obuna tekshirish
@dp.callback_query(lambda c: c.data == "check_subs")
async def check_subscription(callback: types.CallbackQuery):
    try:
        member = await bot.get_chat_member(chat_id="@yourchannel", user_id=callback.from_user.id)
        if member.status in ["member", "administrator", "creator"]:
            menu = ReplyKeyboardMarkup(resize_keyboard=True)
            menu.add(
                KeyboardButton("🛒 Buyurtma berish"),
                KeyboardButton("🎮 O‘yinlar"),
                KeyboardButton("💰 Hisobni to‘ldirish"),
                KeyboardButton("💬 Adminga yozish")
            )
            await callback.message.answer("✅ Obuna tasdiqlandi!\nMenyudan tanlang:", reply_markup=menu)
        else:
            await callback.answer("Avval kanalga obuna bo‘ling!", show_alert=True)
    except Exception as e:
        await callback.answer("Kanal topilmadi yoki bot admin emas!", show_alert=True)
        print(e)

# 🔹 Adminga yozish
@dp.message(lambda m: m.text == "💬 Adminga yozish")
async def contact_admin(message: types.Message):
    await message.answer("✍️ Xabaringizni yozing, adminga yuboraman:")

    @dp.message()
    async def forward_to_admin(msg: types.Message):
        if msg.from_user.id != ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"📩 @{msg.from_user.username} dan:\n{msg.text}")
            await msg.answer("✅ Xabaringiz yuborildi!")
        else:
            await msg.answer("Admin sizsiz 😄")

# 🔹 Hisob to‘ldirish
@dp.message(lambda m: m.text == "💰 Hisobni to‘ldirish")
async def deposit(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Payme", callback_data="bank_payme")],
        [InlineKeyboardButton(text="💳 Click", callback_data="bank_click")]
    ])
    await message.answer("To‘lov tizimini tanlang:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("bank_"))
async def bank_choice(callback: types.CallbackQuery):
    bank = callback.data.split("_")[1]
    await callback.message.answer(
        f"💳 Siz {bank.title()} tanladingiz.\n"
        "8600 1234 5678 9000 raqamiga to‘lov qiling va chekni yuboring."
    )

# 🔹 O‘yinlar bo‘limi
@dp.message(lambda m: m.text == "🎮 O‘yinlar")
async def games_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🎲 Qura tashlash", "🏀 Basketbol", "🔙 Ortga")
    await message.answer("🎮 O‘yin tanlang:", reply_markup=kb)

@dp.message(lambda m: m.text == "🎲 Qura tashlash")
async def dice_game(message: types.Message):
    x = random.randint(1, 6)
    await message.answer(f"🎲 Chiqqan son: {x}")

@dp.message(lambda m: m.text == "🏀 Basketbol")
async def basket(message: types.Message):
    result = random.choice(["200 so‘m yutding!", "Yutqazding 😢", "500 so‘m bonus!"])
    await message.answer(f"🏀 Natija: {result}")

# 🔹 Buyurtma berish
@dp.message(lambda m: m.text == "🛒 Buyurtma berish")
async def order_cmd(message: types.Message):
    await message.answer("🛍 Buyurtmangizni yozing, tez orada admin javob beradi.")

# 🔹 Botni ishga tushurish
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
