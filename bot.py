import asyncio
import json
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
)
from pathlib import Path

# ⚙️ Sozlamalar
BOT_TOKEN = "8395937326:AAHdugyvBwwTkoM5sFsK3Gu3WrV30TPTSTc"
ADMIN_ID = 7973934849
PAYMENT_PROVIDER_TOKEN = "YOUR_PAYMENT_PROVIDER_TOKEN"  # @BotFather dan olingan token
BOT_USERNAME = "StarstUZBbot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
CHANNEL_FILE = DATA_DIR / "channels.json"

def load_channels():
    if CHANNEL_FILE.exists():
        return json.loads(CHANNEL_FILE.read_text())
    return []

def save_channels(channels):
    CHANNEL_FILE.write_text(json.dumps(channels, indent=2))

# 🔘 Asosiy menyu
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Xarid qilish"), KeyboardButton(text="💼 Hisobim")],
        [KeyboardButton(text="🤝 Hamkorlik dasturi"), KeyboardButton(text="📘 Yo‘riqnoma")]
    ],
    resize_keyboard=True
)

# 🔹 Start komandasi
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    channels = load_channels()
    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except:
            pass

    if not_subscribed:
        markup = InlineKeyboardMarkup()
        for ch in not_subscribed:
            markup.add(InlineKeyboardButton(text=f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}"))
        markup.add(InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subs"))
        await message.answer("⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:", reply_markup=markup)
        return

    await message.answer_photo(
        photo="https://i.ibb.co/GVHvJ3M/stars-banner.jpg",
        caption="⭐️ Xush kelibsiz!\nBu bot orqali siz Telegram Stars, Premium, Emoji va Sticker xizmatlarini xarid qilishingiz mumkin!",
        reply_markup=main_menu
    )

# 🔹 Obuna tekshirish
@dp.callback_query(F.data == "check_subs")
async def check_subs(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    channels = load_channels()
    not_subscribed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status in ("left", "kicked"):
                not_subscribed.append(ch)
        except:
            pass

    if not not_subscribed:
        await callback.message.edit_text("✅ Obuna tekshirildi. Endi botdan foydalanishingiz mumkin.")
        await callback.message.answer("Asosiy menyu:", reply_markup=main_menu)
    else:
        await callback.answer("❌ Hali barcha kanallarga obuna bo‘lmagansiz.", show_alert=True)

# 🔹 Admin panel
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Siz admin emassiz.")
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo‘shish", callback_data="add_channel")],
        [InlineKeyboardButton(text="➖ Kanal o‘chirish", callback_data="del_channel")],
        [InlineKeyboardButton(text="📋 Kanal ro‘yxati", callback_data="list_channels")]
    ])
    await message.answer("🛠 Admin panel", reply_markup=markup)

@dp.callback_query(F.data == "add_channel")
async def add_channel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("📨 Kanal username kiriting (@ bilan):")
    dp.message.register(wait_channel_name)

async def wait_channel_name(message: types.Message):
    ch = message.text.strip()
    if not ch.startswith("@"):
        return await message.answer("❌ Kanal nomi '@' bilan boshlansin.")
    channels = load_channels()
    if ch not in channels:
        channels.append(ch)
        save_channels(channels)
        await message.answer(f"✅ {ch} qo‘shildi.")
    else:
        await message.answer("⚠️ Bu kanal allaqachon mavjud.")
    dp.message.unregister(wait_channel_name)

@dp.callback_query(F.data == "del_channel")
async def del_channel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        return await callback.message.answer("📭 Kanal ro‘yxati bo‘sh.")
    markup = InlineKeyboardMarkup()
    for ch in channels:
        markup.add(InlineKeyboardButton(text=f"❌ {ch}", callback_data=f"rem_{ch}"))
    await callback.message.answer("O‘chiriladigan kanalni tanlang:", reply_markup=markup)

@dp.callback_query(F.data.startswith("rem_"))
async def rem_channel(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    ch = callback.data.replace("rem_", "")
    channels = load_channels()
    if ch in channels:
        channels.remove(ch)
        save_channels(channels)
        await callback.message.answer(f"✅ {ch} o‘chirildi.")

@dp.callback_query(F.data == "list_channels")
async def list_channels(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        await callback.message.answer("📭 Hozircha kanal yo‘q.")
    else:
        await callback.message.answer("📋 Kanal ro‘yxati:\n" + "\n".join(channels))

# 🔹 Xizmatlar (to‘lov tizimi)
@dp.message(F.text == "🛒 Xarid qilish")
async def buy_menu(message: types.Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Telegram Stars - 5$", callback_data="buy_stars")],
        [InlineKeyboardButton(text="💎 Telegram Premium - 4$", callback_data="buy_premium")],
        [InlineKeyboardButton(text="😂 Emoji Pack - 2$", callback_data="buy_emoji")]
    ])
    await message.answer("🛍 Xizmat tanlang:", reply_markup=markup)

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    service = callback.data.replace("buy_", "")
    titles = {
        "stars": ("Telegram Stars", 500),
        "premium": ("Telegram Premium", 400),
        "emoji": ("Emoji Pack", 200)
    }
    title, price_cents = titles.get(service, ("Xizmat", 100))
    prices = [LabeledPrice(label=title, amount=price_cents * 100)]
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title,
        description=f"{title} uchun to‘lov",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="usd",
        prices=prices,
        start_parameter="purchase",
        payload=f"service_{service}"
    )

@dp.pre_checkout_query(lambda q: True)
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
    service = message.successful_payment.invoice_payload.replace("service_", "")
    await message.answer(f"✅ {service.title()} muvaffaqiyatli xarid qilindi!\nAdmin sizga tez orada xizmatni yetkazadi.")
    await bot.send_message(ADMIN_ID, f"💰 Foydalanuvchi @{message.from_user.username} {service} uchun to‘lov qildi.")

@dp.message(F.text == "💼 Hisobim")
async def account(message: types.Message):
    await message.answer("💼 Sizning hisobingiz: 0 yulduz.\nBalansni to‘ldirish uchun to‘lovni amalga oshiring.")

@dp.message(F.text == "🤝 Hamkorlik dasturi")
async def partner(message: types.Message):
    ref_link = f"https://t.me/{BOT_USERNAME}?start={message.from_user.id}"
    await message.answer(f"🤝 Hamkorlik dasturi:\nDo‘stlaringizni taklif qiling!\nSizning referal linkingiz:\n{ref_link}")

@dp.message(F.text == "📘 Yo‘riqnoma")
async def help_info(message: types.Message):
    await message.answer("📘 Yo‘riqnoma:\n1️⃣ Xizmat tanlang\n2️⃣ To‘lovni amalga oshiring\n3️⃣ Xizmatni oling ✅")

# 🚀 Ishga tushirish
async def main():
    print("🚀 Bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
