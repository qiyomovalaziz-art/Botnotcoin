import telebot
from telebot import types

TOKEN = "7589550087:AAERu7icdx5z9Ye_hfM7-FwNwgtJVja0R_M"  # bu joyga o'z tokeningni yoz
bot = telebot.TeleBot(TOKEN)

# Har bir user uchun coin saqlanadi
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = 0
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton("💰 Coin yig‘ish")
    markup.add(btn)
    bot.send_message(message.chat.id, "Salom! Bosib coin yig‘ing 💸", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_click(message):
    user_id = message.from_user.id
    if message.text == "💰 Coin yig‘ish":
        user_data[user_id] += 1
        bot.send_message(message.chat.id, f"Sizda {user_data[user_id]} ta coin bor! 💰")
    else:
        bot.send_message(message.chat.id, "💬 Tugmani bosing coin olish uchun!")

bot.infinity_polling()
