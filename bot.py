import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "7950741525:AAGS1PTIS85C5-fTnX525GckAFTZ2ebNpNY"
ADMIN_ID = 2127850181

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# DATABASE
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer INTEGER,
    referrals INTEGER DEFAULT 0
)
""")
conn.commit()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    args = message.get_args()
    user_id = message.from_user.id

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        await message.answer("👋 Siz allaqachon ro‘yxatdan o‘tgansiz")
        return

    referrer = int(args) if args.isdigit() else None

    cursor.execute(
        "INSERT INTO users (user_id, referrer) VALUES (?,?)",
        (user_id, referrer)
    )

    if referrer:
        cursor.execute(
            "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
            (referrer,)
        )

    conn.commit()

    await message.answer(
        "🎉 Referal Bozori botiga xush kelibsiz!\n\n"
        "💰 Referal silka narxi: 3000 so‘m\n"
        "👥 10 ta odam taklif qiling\n"
        "💳 15 000 so‘m Click orqali to‘lanadi"
    )

@dp.message_handler(commands=['link'])
async def link(message: types.Message):
    user_id = message.from_user.id
    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user_id}"
    await message.answer(f"🔗 Sizning referal linkingiz:\n{link}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
