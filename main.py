import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- FLASK KEEP ALIVE CODE ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and Database is connected!"

def run():
  app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --------------------------------------------

# --- BOT & DATABASE SETUP ---
TOKEN = "8431815261:AAGrAJHFOx153xKTn1t_x_N3siHe2XXaSQY"
CHANNEL_USERNAME = "@saniwall_23"
bot = telebot.TeleBot(TOKEN)

# Aapka Corrected MongoDB Link (Password with %40)
MONGO_URI = "mongodb+srv://Mybott:Mybott.%40.com@mybotdata.21olkh5.mongodb.net/?appName=MyBotData" 

client = MongoClient(MONGO_URI)
db = client['telegram_bot']
collection = db['wallpapers']

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

# 👑 ADMIN: Upload image/video
@bot.message_handler(content_types=['photo', 'video', 'document'])
def save_media(message):
    if not is_admin(message.from_user.id): return

    if message.caption:
        file_code = message.caption.strip().split()[0] 

        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            file_id = message.video.file_id
        else:
            file_id = message.document.file_id

        # MongoDB me data hamesha ke liye save karna
        collection.update_one(
            {"_id": file_code},
            {"$set": {"file_id": file_id, "type": message.content_type}},
            upsert=True
        )

        bot_username = bot.get_me().username
        link = f"https://t.me/{bot_username}?start={file_code}"

        bot.reply_to(message, f"✅ **Saved in Database as: {file_code}**\n\nLink for Channel:\n`{link}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Caption mein number likho (e.g. 1)")

# 👥 USER: Get file
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.from_user.id
    text = message.text

    if text.startswith('/start'):
        parts = text.split()
        file_code = parts[1] if len(parts) > 1 else None
    else:
        file_code = text.strip()

    # --- PROFESSIONAL WELCOME MESSAGE ---
    if not file_code:
        welcome_msg = (
            "🌟 **Welcome to Saniwall!** 🌟\n\n"
            "Yahan aapko best HD Wallpapers aur content milega.\n"
            "👉 Kripya channel se post ka link click karein ya direct file code bhejein."
        )
        bot.reply_to(message, welcome_msg, parse_mode="Markdown")
        return

    # Check Join
    if not check_join(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💎 Join Channel", url=f"https://t.me/saniwall_23"))
        bot.reply_to(message, "🚫 Pehle channel join karein!", reply_markup=markup)
        return

    # MongoDB se data nikalna
    file_data = collection.find_one({"_id": file_code})

    if file_data:
        try:
            if file_data['type'] == 'photo': bot.send_photo(message.chat.id, file_data['file_id'])
            elif file_data['type'] == 'video': bot.send_video(message.chat.id, file_data['file_id'])
            else: bot.send_document(message.chat.id, file_data['file_id'])
        except Exception as e:
            # --- SERVER DOWN ERROR ---
            bot.reply_to(message, "❌ **Server Down!**\nAbhi file bhejne me problem ho rahi hai. Kripya thodi der baad try karein.", parse_mode="Markdown")
    else:
        # --- FILE NOT FOUND ERROR ---
        error_msg = (
            "⚠️ **File Not Found!**\n\n"
            f"Aapne jo code bheja hai (`{file_code}`), wo galat hai ya file delete ho chuki hai.\n"
            "Kripya sahi link use karein."
        )
        bot.reply_to(message, error_msg, parse_mode="Markdown")

print("🚀 Bot Started with MongoDB Database!")
keep_alive() 
bot.polling(none_stop=True)
