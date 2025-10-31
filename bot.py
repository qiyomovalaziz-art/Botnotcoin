from flask import Flask, request, send_from_directory, jsonify
import telebot
import sqlite3
import os

TOKEN = "7589550087:AAERu7icdx5z9Ye_hfM7-FwNwgtJVja0R_M"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === DATABASE ===
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins INTEGER DEFAULT 0)")
conn.commit()

# === TELEGRAM COMMAND ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, ?)", (user_id, 0))
    conn.commit()

    webapp_url = "https://botnotcoin-production.up.railway.app/"  # bu senga tegishli link
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🎮 O‘yinni boshlash", web_app=telebot.types.WebAppInfo(webapp_url))
    markup.add(btn)
    bot.send_message(message.chat.id, "Salom! Bosing va coin yig‘ing 💰", reply_markup=markup)

# === FLASK ROUTES ===
@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def send_file(path):
    return send_from_directory('web', path)

@app.route('/add_coin', methods=['POST'])
def add_coin():
    data = request.json
    user_id = data.get("user_id")
    cursor.execute("UPDATE users SET coins = coins + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    coins = cursor.fetchone()[0]
    return jsonify({"coins": coins})

if __name__ == '__main__':
    import threading
    threading.Thread(target=lambda: bot.polling(non_stop=True)).start()
    app.run(host='0.0.0.0', port=8080)
