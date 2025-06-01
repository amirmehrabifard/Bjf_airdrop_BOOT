import os
import telebot
import psycopg2
from web3 import Web3

# 🔹 تنظیمات اولیه
BOT_TOKEN = "YOUR_BOT_TOKEN"  # جایگزین با توکن ربات
CHANNEL_USERNAME = "@benjaminfranklintoken"
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
AIRDROP_WALLET = "0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544"

# 🔹 اتصال به تلگرام
bot = telebot.TeleBot(BOT_TOKEN)

# 🔹 تنظیم پایگاه داده
conn = psycopg2.connect(
    dbname="your_db_name",
    user="your_db_user",
    password="your_db_password",
    host="your_db_host",
    port="5432"
)
cursor = conn.cursor()

# 🔹 بررسی عضویت در کانال
def check_membership(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🔹 خوش‌آمدگویی و ساخت لینک دعوت
@bot.message_handler(commands=['start'])
def welcome_user(message):
    user_id = message.chat.id
    
    if check_membership(user_id):
        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (user_id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            invite_link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
            cursor.execute("INSERT INTO users (telegram_id, invite_link, tokens_received) VALUES (%s, %s, %s)",
                           (user_id, invite_link, 500))
            conn.commit()

            welcome_text = f"✅ خوش آمدید! ۵۰۰ توکن BJF دریافت کردید.\nلینک دعوت شما: {invite_link}\n"
            bot.send_message(user_id, welcome_text)
        else:
            bot.send_message(user_id, "❌ شما قبلاً ثبت نام کرده‌اید!")
    else:
        bot.send_message(user_id, "⚠️ ابتدا باید در کانال @benjaminfranklintoken عضو شوید!")

bot.polling()
