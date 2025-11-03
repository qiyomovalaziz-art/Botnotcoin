import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 🧑‍💼 ADMIN ID — o'zingizning Telegram ID raqamingizni kiriting!
ADMIN_ID = 7973934849  

# 🧍‍♂️ Foydalanuvchilar ro'yxati
users = set()

# 📨 Admin tomonidan yuboriladigan xabar
admin_message = "Hozircha xabar yo‘q."

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)
    await update.message.reply_text("✅ Siz botga obuna bo‘ldingiz. Admin xabarlarini olasiz!")

# /setmsg komandasi
async def setmsg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global admin_message
    if update.effective_user.id == ADMIN_ID:
        if context.args:
            admin_message = " ".join(context.args)
            await update.message.reply_text(f"✅ Yangi xabar o‘rnatildi:\n\n{admin_message}")
        else:
            await update.message.reply_text("❗ Foydalanish: /setmsg [xabar matni]")
    else:
        await update.message.reply_text("⛔ Siz admin emassiz!")

# 🔁 Har 1 sekundda xabar yuborish funksiyasi
async def send_messages(app):
    global admin_message
    while True:
        for user_id in list(users):
            try:
                await app.bot.send_message(chat_id=user_id, text=admin_message)
            except Exception:
                pass
        await asyncio.sleep(1)  # 1 sekund kutadi

# 🚀 Asosiy funksiya
async def main():
    # ❗ SHU YERGA TOKENINGIZNI QO‘YING ❗
    app = Application.builder().token("8379130776:AAE9rme01SfeUmVoR6F92hbU5_rnU2z-Uh4").build()

    # Komandalar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setmsg", setmsg))

    # Orqa fonda xabar yuborishni ishga tushiramiz
    asyncio.create_task(send_messages(app))

    print("🤖 Bot ishga tushdi...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
