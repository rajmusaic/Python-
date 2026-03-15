import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from flask import Flask         # Render trick ke liye add kiya
from threading import Thread    # Render trick ke liye add kiya

# --- FLASK KEEP ALIVE CODE (Render trick) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --------------------------------------------

TOKEN = "8431815261:AAGrAJHFOx153xKTn1t_x_N3siHe2XXaSQY"
CHANNEL_USERNAME = "@saniwall_23"
bot = telebot.TeleBot(TOKEN)
DB_FILE = "wall_data.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

def is_admin(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['administrator', 'creator']
    except: return False

def check_join(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# 👑 ADMIN: Upload image/video with number in caption
@bot.message_handler(content_types=['photo', 'video', 'document'])
def save_media(message):
    if not is_admin(message.from_user.id): return
    db = load_db()
    
    if message.caption:
        file_code = message.caption.strip().split()[0] 
        
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            file_id = message.video.file_id
        else:
            file_id = message.document.file_id
            
        db[file_code] = {"id": file_id, "type": message.content_type}
        save_db(db)
        
        bot_username = bot.get_me().username
        link = f"https://t.me/{bot_username}?start={file_code}"
        
        bot.reply_to(message, f"✅ **Saved as: {file_code}**\n\nLink for Channel:\n`{link}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Caption mein number likho (e.g. 1)")

# 👥 USER: Get file when clicking link or typing code
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.from_user.id
    text = message.text
    
    # Extract code from /start link or direct text
    if text.startswith('/start'):
        parts = text.split()
        file_code = parts[1] if len(parts) > 1 else None
    else:
        file_code = text.strip()

    if not file_code:
        bot.reply_to(message, "Welcome! Code bhejiye.")
        return

    # Check Join
    if not check_join(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💎 Join Channel", url=f"https://t.me/saniwall_23"))
        bot.reply_to(message, "🚫 Pehle channel join karein!", reply_markup=markup)
        return

    db = load_db()
    if file_code in db:
        file = db[file_code]
        try:
            if file['type'] == 'photo': bot.send_photo(message.chat.id, file['id'])
            elif file['type'] == 'video': bot.send_video(message.chat.id, file['id'])
            else: bot.send_document(message.chat.id, file['id'])
        except:
            bot.reply_to(message, "❌ Error sending file.")
    else:
        # Agar user sirf /start likhta hai toh error na dikhaye
        if not text.startswith('/start'):
            bot.reply_to(message, f"❌ Invalid Code: {file_code}")

print("🚀 Bot Started Successfully!")
keep_alive() # Render trick start karne ke liye
bot.polling(none_stop=True)
