import os
import telebot
import psycopg2
from web3 import Web3

# 🔹 تنظیمات ربات و بلاکچین
BOT_TOKEN = "YOUR_BOT_TOKEN"  # توکن ربات را جایگزین کنید
CHANNEL_USERNAME = "@benjaminfranklintoken"
CONTRACT_ADDRESS = "0xd5baB4C1b92176f9690c0d2771EDbF18b73b8181"
AIRDROP_WALLET = "0xd5F168CFa6a68C21d7849171D6Aa5DDc9307E544"
WEB3_PROVIDER = "https://bsc-dataseed.binance.org/"  # نود عمومی شبکه BNB
PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # کلید خصوصی از متغیرهای محیطی خوانده شود

# 🔹 اتصال به تلگرام
bot = telebot.TeleBot(BOT_TOKEN)

# 🔹 اتصال به پایگاه داده
conn = psycopg2.connect(
    dbname="your_db_name",
    user="your_db_user",
    password="your_db_password",
    host="your_db_host",
    port="5432"
)
cursor = conn.cursor()

# 🔹 اتصال به شبکه BNB
web3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
contract_abi = [...]  # اینجا ABI توکن وارد شود
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# 🔹 بررسی عضویت در کانال
def check_membership(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🔹 ارسال توکن به کاربر
def send_tokens(user_wallet, amount):
    nonce = web3.eth.get_transaction_count(AIRDROP_WALLET)
    tx = contract.functions.transfer(user_wallet, amount).build_transaction({
        'chainId': 56,
        'gas': 200000,
        'gasPrice': web3.to_wei('5', 'gwei'),
        'nonce': nonce
    })
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return web3.to_hex(tx_hash)

# 🔹 خوش‌آمدگویی و ارسال توکن اولیه
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

            tx_hash = send_tokens(AIRDROP_WALLET, 500 * (10**18))
            cursor.execute("INSERT INTO transactions (telegram_id, transaction_hash, amount, status) VALUES (%s, %s, %s, %s)",
                           (user_id, tx_hash, 500, "Completed"))
            conn.commit()

            welcome_text = f"✅ خوش آمدید! ۵۰۰ توکن BJF دریافت کردید.\nلینک دعوت شما: {invite_link}\n"
            bot.send_message(user_id, welcome_text)
        else:
            bot.send_message(user_id, "❌ شما قبلاً ثبت نام کرده‌اید!")
    else:
        bot.send_message(user_id, "⚠️ ابتدا باید در کانال @benjaminfranklintoken عضو شوید!")

# 🔹 مدیریت دعوت‌ها و ارسال توکن
@bot.message_handler(commands=['invite'])
def manage_invite(message):
    inviter_id = message.chat.id
    invitee_id = message.text.split(" ")[1] if len(message.text.split()) > 1 else None

    if invitee_id:
        cursor.execute("SELECT * FROM invites WHERE invitee_id = %s", (invitee_id,))
        invite_exists = cursor.fetchone()

        if not invite_exists:
            cursor.execute("INSERT INTO invites (inviter_id, invitee_id, status) VALUES (%s, %s, %s)",
                           (inviter_id, invitee_id, "Valid"))
            conn.commit()

            tx_hash = send_tokens(AIRDROP_WALLET, 100 * (10**18))
            cursor.execute("INSERT INTO transactions (telegram_id, transaction_hash, amount, status) VALUES (%s, %s, %s, %s)",
                           (inviter_id, tx_hash, 100, "Completed"))
            conn.commit()

            bot.send_message(inviter_id, "✅ دعوت موفق! ۱۰۰ توکن BJF به حساب شما ارسال شد.")
        else:
            bot.send_message(inviter_id, "❌ این دعوت قبلاً ثبت شده است.")
    else:
        bot.send_message(inviter_id, "❌ خطا در دریافت شناسه دعوت‌شونده!")

bot.polling()
