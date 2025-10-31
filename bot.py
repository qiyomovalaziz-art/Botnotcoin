# bot.py
from flask import Flask, request, send_from_directory, jsonify
import telebot
import sqlite3
import threading
import os
import time
import random
from datetime import datetime, timedelta, date

# ====== CONFIG ======
TOKEN = os.environ.get("BOT_TOKEN")  # Railway Variables ga qo'y
WEBAPP_URL = os.environ.get("WEBAPP_URL")  # misol: https://botnotcoin-production.up.railway.app
# Game settings
MAX_ENERGY = 10
ENERGY_REGEN_SECONDS = 60 * 5  # 1 energy per 5 minutes (300s). Istasangiz 60*1 = 1min qilib o'zgartiring
DAILY_BONUS_COINS = 50
REFERRAL_REWARD_REFERRER = 50
REFERRAL_REWARD_NEW = 20
MIN_CLICK_REWARD = 1
MAX_CLICK_REWARD = 5

if not TOKEN:
    raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisi topilmadi. Railway Variables ga qo'ying.")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ====== DATABASE (SQLite) ======
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0,
    energy INTEGER DEFAULT ?,
    last_energy_ts INTEGER DEFAULT 0,
    invited_by INTEGER DEFAULT NULL,
    last_daily TEXT DEFAULT NULL
)
""", (MAX_ENERGY,))
# Not all SQLite drivers accept parameter in CREATE; if error, we will run an alternative:
try:
    conn.commit()
except Exception:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 0,
        energy INTEGER DEFAULT 10,
        last_energy_ts INTEGER DEFAULT 0,
        invited_by INTEGER DEFAULT NULL,
        last_daily TEXT DEFAULT NULL
    )
    """)
    conn.commit()

# Helper functions
def ensure_user(user_id, invited_by=None):
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users (user_id, coins, energy, last_energy_ts, invited_by, last_daily) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, 0, MAX_ENERGY, int(time.time()), invited_by, None)
        )
        conn.commit()

def get_user(user_id):
    cursor.execute("SELECT user_id, coins, energy, last_energy_ts, invited_by, last_daily FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "user_id": row[0],
        "coins": row[1],
        "energy": row[2],
        "last_energy_ts": row[3],
        "invited_by": row[4],
        "last_daily": row[5]
    }

def regen_energy_for_user(user):
    """Return updated energy after regeneration calculation (but do not persist automatically)."""
    now = int(time.time())
    last = user['last_energy_ts'] or now
    energy = user['energy']
    if energy >= MAX_ENERGY:
        return energy
    # seconds since last update
    elapsed = now - last
    gained = elapsed // ENERGY_REGEN_SECONDS
    if gained > 0:
        new_energy = min(MAX_ENERGY, energy + gained)
        # update DB: set new energy and update last_energy_ts
        new_last = last + gained * ENERGY_REGEN_SECONDS
        cursor.execute("UPDATE users SET energy = ?, last_energy_ts = ? WHERE user_id = ?", (new_energy, new_last, user['user_id']))
        conn.commit()
        return new_energy
    return energy

# ====== TELEGRAM HANDLERS ======
@bot.message_handler(commands=['start'])
def handle_start(message):
    # /start or /start <referrer_id>
    args = message.text.split()
    user_id = message.from_user.id
    invited_by = None
    if len(args) > 1:
        try:
            invited_by = int(args[1])
        except:
            invited_by = None

    ensure_user(user_id, invited_by)

    # If new registration with invited_by and referrer exists -> reward
    if invited_by and invited_by != user_id:
        # ensure referrer exists
        ensure_user(invited_by)
        # add rewards only if this user was newly created and invited_by not null and not same
        # To avoid rewarding repeatedly, we only reward if user's coins == 0 (just created)
        u = get_user(user_id)
        if u and u['coins'] == 0:
            cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (REFERRAL_REWARD_NEW, user_id))
            cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (REFERRAL_REWARD_REFERRER, invited_by))
            conn.commit()
            try:
                bot.send_message(invited_by, f"🎉 Sizga yangi referal qo‘shildi! +{REFERRAL_REWARD_REFERRER} 🪙")
            except:
                pass

    # Prepare keyboard (webapp + callbacks)
    web_url = WEBAPP_URL or ""
    markup = telebot.types.InlineKeyboardMarkup()
    if web_url:
        markup.add(telebot.types.InlineKeyboardButton("🎮 O‘yinni boshlash", web_app=telebot.types.WebAppInfo(web_url)))
    markup.add(
        telebot.types.InlineKeyboardButton("🏆 Reyting", callback_data="leaderboard"),
        telebot.types.InlineKeyboardButton("🔗 Referal", callback_data="referral")
    )
    markup.add(telebot.types.InlineKeyboardButton("👤 Profil", callback_data="profile"))
    bot.send_message(message.chat.id, "Salom! Bosing va coin yig‘ing 💰", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    if call.data == "leaderboard":
        cursor.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10")
        rows = cursor.fetchall()
        text = "🏆 TOP 10:\n\n"
        for i, row in enumerate(rows, start=1):
            uid, coins = row
            # tg://user?id=... orqali username ko'rsatish
            text += f"{i}. 👤 <a href='tg://user?id={uid}'>Player</a> — {coins} 🪙\n"
        bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    elif call.data == "referral":
        me = bot.get_me()
        ref_link = f"https://t.me/{me.username}?start={user_id}"
        bot.send_message(call.message.chat.id, f"🔗 Sizning referal linkingiz:\n{ref_link}")
    elif call.data == "profile":
        ensure_user(user_id)
        user = get_user(user_id)
        regen_energy_for_user(user)  # update energy
        user = get_user(user_id)
        text = f"👤 Profil\n\n🪙 Coin: {user['coins']}\n⚡ Energiya: {user['energy']}/{MAX_ENERGY}\n"
        bot.send_message(call.message.chat.id, text)

# ====== FLASK ROUTES (webapp API) ======
@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('web', path)

@app.route('/add_coin', methods=['POST'])
def add_coin():
    data = request.json or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    ensure_user(user_id)
    user = get_user(user_id)
    # regen energy before using
    current_energy = regen_energy_for_user(user)
    user = get_user(user_id)
    if user['energy'] <= 0:
        return jsonify({"error": "no_energy", "message": "Sizda energiya yo'q. Kutib turing yoki leaderboardga qarang.", "energy": user['energy']}), 403

    # consume 1 energy
    new_energy = user['energy'] - 1
    cursor.execute("UPDATE users SET energy = ?, last_energy_ts = ? WHERE user_id = ?", (new_energy, int(time.time()), user_id))
    conn.commit()

    # give random coins for this click
    added = random.randint(MIN_CLICK_REWARD, MAX_CLICK_REWARD)
    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (added, user_id))
    conn.commit()

    cursor.execute("SELECT coins, energy FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    coins, energy = row
    return jsonify({"coins": coins, "added": added, "energy": energy})

@app.route('/profile/<int:uid>', methods=['GET'])
def api_profile(uid):
    user = get_user(uid)
    if not user:
        return jsonify({"error": "not_found"}), 404
    # regen
    regen_energy_for_user(user)
    user = get_user(uid)
    return jsonify({
        "user_id": user['user_id'],
        "coins": user['coins'],
        "energy": user['energy'],
        "invited_by": user['invited_by'],
        "last_daily": user['last_daily']
    })

@app.route('/daily_claim', methods=['POST'])
def daily_claim():
    data = request.json or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    ensure_user(user_id)
    user = get_user(user_id)
    today_str = date.today().isoformat()
    if user['last_daily'] == today_str:
        return jsonify({"error": "already_claimed", "message": "Bugun daily allaqachon olgansiz."}), 403
    # give daily bonus
    cursor.execute("UPDATE users SET coins = coins + ?, last_daily = ? WHERE user_id = ?", (DAILY_BONUS_COINS, today_str, user_id))
    conn.commit()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,))
    coins = cursor.fetchone()[0]
    return jsonify({"coins": coins, "daily": DAILY_BONUS_COINS})

@app.route('/leaderboard', methods=['GET'])
def api_leaderboard():
    cursor.execute("SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 20")
    rows = cursor.fetchall()
    result = [{"rank": i+1, "user_id": r[0], "coins": r[1]} for i, r in enumerate(rows)]
    return jsonify(result)

# ====== RUN BOT + FLASK ======
def run_bot_polling():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot_polling, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
