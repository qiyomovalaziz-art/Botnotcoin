from flask import Flask, request, send_from_directory, jsonify
import telebot
import sqlite3
import threading

TOKEN = "7589550087:AAERu7icdx5z9Ye_hfM7-FwNwgtJVja0R_M"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === DATABASE ===
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")
conn.commit()

# === TELEGRAM HANDLER ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    args = message.text.split()

    # Agar referal link orqali kirgan bo‘lsa
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])

    cursor.execute("INSERT OR IGNORE INTO users (user_id, coins, invited_by) VALUES (?, ?, ?)", (user_id, 0, referrer_id))
    conn.commit()

    # Referal mukofot
    if referrer_id and referrer_id != user_id:
        cursor.execute("UPDATE users SET coins = coins + 5 WHERE user_id = ?", (referrer_id,))
        conn.commit()
        bot.send_message(referrer_id, f"🎉 Sizning referalingiz orqali yangi foydalanuvchi qo‘shildi! +5 🪙")

    webapp_url = "https://botnotcoin-production.up.railway.app/"
    markup = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton("🎮 O‘yinni boshlash", web_app=telebot.types.WebAppInfo(webapp_url))
    btn2 = telebot.types.InlineKeyboardButton("🏆 Reyting", callback_data="leaderboard")
    btn3 = telebot.types.InlineKeyboardButton("🔗 Referal havola", callback_data="referral")
    markup.add(btn1)
    markup.add(btn2, btn3)
    bot.send_message(message.chat.id, "Salom! Boshlaymizmi? 💰", reply_markup=markup)

# === CALLBACKLAR ===
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "leaderboard":
        cursor.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10")
        rows = cursor.fetchall()
        text = "🏆 Eng boy o‘yinchilar:\n\n"
        for i, row in enumerate(rows, start=1):
            text += f"{i}. 👤 <a href='tg://user?id={row[0]}'>Foydalanuvchi</a> — {row[1]} 🪙\n"
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")

    elif call.data == "referral":
        ref_link = f"https://t.me/{bot.get_me().username}?start={call.from_user.id}"
        bot.send_message(call.message.chat.id, f"🔗 Sizning referal linkingiz:\n{ref_link}")

# === FLASK WEB-APP ===
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

# === ISHGA TUSHIRISH ===
if __name__ == '__main__':
    threading.Thread(target=lambda: bot.polling(non_stop=True)).start()
    app.run(host='0.0.0.0', port=8080)
