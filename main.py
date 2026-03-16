import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from flask import Flask
from threading import Thread
from pymongo import MongoClient

# --- FLASK KEEP ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIG ---
TOKEN = "8431815261:AAGrAJHFOx153xKTn1t_x_N3siHe2XXaSQY"
CHANNEL_USERNAME = "@saniwall_23"
# Is password mein @ ki jagah %40 pehle se kar diya hai
MONGO_URI = "mongodb+srv://Mybott:Mybott.%40.com@mybotdata.21olkh5.mongodb.net/?appName=MyBotData"

bot = telebot.TeleBot(TOKEN)
client = MongoClient(MONGO_URI)
db = client['telegram_bot']
collection = db['wallpapers']

# --- PERMANENT ADMIN CHECK ---
def is_admin(user_id):
    # Aapki ID (1751276228) ko direct permission de di hai
    if str(user_id) == "1751276228":
        return True
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['administrator', 'creator']
    except:
        return False

def check_join(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# 👑 UPLOAD HANDLER
@bot.message_handler(content_types=['photo', 'video', 'document'])
def save_media(message):
    if not is_admin(message.from_user.id):
        return # Agar admin nahi hai to bot kuch nahi karega

    if message.caption:
        file_code = message.caption.strip().split()[0]
        if message.content_type == 'photo': file_id = message.photo[-1].file_id
        elif message.content_type == 'video': file_id = message.video.file_id
        else: file_id = message.document.file_id

        collection.update_one({"_id": file_code}, {"$set": {"file_id": file_id, "type": message.content_type}}, upsert=True)
        
        bot_username = bot.get_me().username
        link = f"https://t.me/{bot_username}?start={file_code}"
        bot.reply_to(message, f"✅ **Saved!**\n\nCode: `{file_code}`\nLink: `{link}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "⚠️ Photo ke saath caption mein code likho!")

# 👥 USER HANDLER
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.from_user.id
    text = message.text

    if text.startswith('/start'):
        parts = text.split()
        file_code = parts[1] if len(parts) > 1 else None
    else:
        file_code = text.strip()

    if not file_code:
        bot.reply_to(message, "🌟 **Welcome to Saniwall!**\n\nKripya channel se link click karein.")
        return

    if not check_join(user_id):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("💎 Join Channel", url=f"https://t.me/saniwall_23"))
        bot.reply_to(message, "🚫 Pehle channel join karein!", reply_markup=markup)
        return

    file_data = collection.find_one({"_id": file_code})
    if file_data:
        try:
            if file_data['type'] == 'photo': bot.send_photo(message.chat.id, file_data['file_id'])
            elif file_data['type'] == 'video': bot.send_video(message.chat.id, file_data['file_id'])
            else: bot.send_document(message.chat.id, file_data['file_id'])
        except:
            bot.reply_to(message, "❌ **Service Down!**")
    else:
        bot.reply_to(message, "⚠️ **File Not Found!**")

keep_alive()
print("🚀 Permanent Bot Started!")
bot.polling(none_stop=True)
