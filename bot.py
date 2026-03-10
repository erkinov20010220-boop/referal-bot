import asyncio
import os
from dotenv import load_dotenv
from keyboards import (
    coin_market_kb,
    referal_kb,
    pul_yechish_kb,
    clicker_inline_kb
)
import datetime
from storage import users
from aiogram.enums import ParseMode
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ContentType
)
from aiogram.filters import CommandStart
from admin import LinkState
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ================= FORMAT FUNCTIONS =================

def format_rc(amount: float) -> str:
    # 4 xonali aniqlik, ortiqcha 0 olib tashlanadi
    text = f"{amount:.4f}"
    text = text.rstrip("0").rstrip(".")
    return text


def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")

# ================= CONFIG =================

load_dotenv()

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
CHANNEL = os.getenv("CHANNEL")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

from coin_market import router as coin_router
dp.include_router(coin_router)

from admin import router as admin_router
dp.include_router(admin_router)

BONUS_RC = 3
BONUS_SUM = 200

# ================= KEYBOARDS =================

def sub_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📢 Kanalga obuna bo‘lish",
                url=f"https://t.me/{CHANNEL.lstrip('@')}"
            )],
            [InlineKeyboardButton(
                text="✅ Tekshirish",
                callback_data="check_sub"
            )]
        ]
    )

def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="📲 Raqamni yuborish",
                request_contact=True
            )]
        ],
        resize_keyboard=True
    )

def main_menu(uid):
    buttons = [
        [KeyboardButton(text="🪙 Coin Market")],
        [KeyboardButton(text="🛒 Referal sotib olish"),
         KeyboardButton(text="🎁 Bonus olish")],
        [KeyboardButton(text="💳 Pul yechish"),
         KeyboardButton(text="💰 Balans")],
        [KeyboardButton(text="ℹ️ Bot haqida")]
    ]

    if uid == ADMIN_ID:
        buttons.append([KeyboardButton(text="👨‍💻 ADMIN PANELI")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ================= ACCESS CHECK =================

async def check_access(uid, send_message=True):

    users.setdefault(uid, {
    "sub": False,
    "phone": False,
    "rc_balance": 0,
    "money_balance": 0,
    "last_bonus": None,
    "referrer": None,
    "referrals": [],
    "reward_given": False
})
    # Kanal tekshiruv
    try:
        member = await bot.get_chat_member(
            f"@{CHANNEL.lstrip('@')}",
            uid
        )
        users[uid]["sub"] = member.status in [
            "member", "administrator", "creator"
        ]
    except:
        users[uid]["sub"] = False

    if not users[uid]["sub"]:
        if send_message:
            await bot.send_message(
                uid,
                "⛔ Botdan foydalanish uchun kanalga obuna bo‘ling:",
                reply_markup=sub_kb()
            )
        return False

    # Telefon tekshiruv
    if not users[uid]["phone"]:
        if send_message:
            await bot.send_message(
                uid,
                "📱 Telefon raqamingizni yuboring:",
                reply_markup=phone_kb()
            )
        return False

    return True

# ================= START =================
@dp.message(CommandStart())
async def start_handler(message: Message):

    uid = message.from_user.id
    args = message.text.split()

    referrer = None

    if len(args) > 1:
        try:
            referrer = int(args[1])
        except:
            pass

    if uid not in users:

        users[uid] = {
            "sub": False,
            "phone": False,
            "rc_balance": 0,
            "money_balance": 0,
            "last_bonus": None,
            "referrer": referrer,
            "referrals": [],
            "reward_given": False
        }

        if referrer and referrer != uid and referrer in users:
            users[referrer]["referrals"].append(uid)

    if not await check_access(uid):
        return

    await message.answer(
        "✅ Asosiy menyu:",
        reply_markup=main_menu(uid)
    )
# ================= PHONE =================

@dp.message(F.content_type == ContentType.CONTACT)
async def phone_handler(message: Message):

    uid = message.from_user.id

    users.setdefault(uid, {
    "sub": False,
    "phone": False,
    "rc_balance": 0,
    "money_balance": 0,
    "last_bonus": None,
    "referrer": None,
    "referrals": [],
    "reward_given": False
})
    users[uid]["phone"] = True

    await message.answer(
        "✅ Telefon tasdiqlandi!",
        reply_markup=main_menu(uid)
    )

# ================= CHECK SUB =================

@dp.callback_query(F.data == "check_sub")
async def check_sub(call):

    uid = call.from_user.id

    try:
        member = await bot.get_chat_member(
            f"@{CHANNEL.lstrip('@')}",
            uid
        )

        if member.status in ["member", "administrator", "creator"]:
            users[uid]["sub"] = True
            await call.message.delete()

            if users[uid].get("phone"):
                await bot.send_message(
                    uid,
                    "📋 Asosiy menyu:",
                    reply_markup=main_menu(uid)
                )
            else:
                await bot.send_message(
                    uid,
                    "📱 Telefon raqamingizni yuboring:",
                    reply_markup=phone_kb()
                )
            return

    except:
        pass

    await call.answer("❌ Avval kanalga obuna bo‘ling!", show_alert=True)

################ Toʻxtatish ###############

@dp.callback_query(F.data == "stop_timer")
async def stop_mini_game(call: CallbackQuery):
    uid = call.from_user.id
    now = datetime.datetime.now()

    if uid not in mini_game_state:
        await call.answer("⚠️ O‘yin hali boshlanmadi.", show_alert=True)
        return

    game = mini_game_state[uid]
    stop_time = now.time()
    target_time = game["target"]
    start_time = game["start"]
    end_time = game["end"]

    # O‘yin oralig‘ini tekshirish
    if not (start_time <= stop_time <= end_time):
        await call.answer("❌ O‘yin vaqti 00:00:00 - 00:15:00 oralig‘ida bo‘lishi kerak!", show_alert=True)
        return

    # Sekundga o‘girish
    target_seconds = target_time.hour*3600 + target_time.minute*60 + target_time.second
    stop_seconds = stop_time.hour*3600 + stop_time.minute*60 + stop_time.second

    # 1 soniya ruxsat
    if abs(stop_seconds - target_seconds) <= 1 and not game["reward_given"]:
        state = clicker_state.setdefault(uid, {
            "click_count": 0,
            "pause_until": None,
            "daily_rc": 0.0,
            "daily_reset": now.date(),
        })

        reward = 50.0
        if state["daily_rc"] + reward > MAX_DAILY_RC:
            reward = MAX_DAILY_RC - state["daily_rc"]
            if reward <= 0:
                await call.answer("🚫 Kunlik limit tugadi! RC ololmadingiz.", show_alert=True)
                mini_game_state.pop(uid, None)
                await call.message.edit_reply_markup(reply_markup=None)
                return

        users[uid]["rc_balance"] += reward
        state["daily_rc"] += reward
        game["reward_given"] = True

        await call.answer(f"🎉 To‘g‘ri vaqtni ushladingiz! +{int(reward)} RC", show_alert=True)
    else:
        await call.answer(
            "❌ Xato vaqt, afsus! Qayta urinib ko‘ring.\n"
            "Tip: Maqsad vaqt 00:10:00",
            show_alert=True
        )

    # Tugmani olib tashlash va o‘yin holatini tozalash
    await call.message.edit_reply_markup(reply_markup=None)
    mini_game_state.pop(uid, None)

#PUL YECHISH

@dp.message(F.text == "💳 Pul yechish")
async def pul_yechish(message: Message):

    uid = message.from_user.id

    if not await check_access(uid):
        return

    await message.answer(
        "💳 Pul yechish bo‘limi:",
        reply_markup=pul_yechish_kb()
    )

#Referal sotib olish

@dp.message(F.text == "🛒 Referal sotib olish")
async def referal(message: Message):

    text = """
🛒 <b>Referal havolani sotib olish:</b>

Referal havola orqali cheksiz foydalanuvchilarni taklif qilib, doimiy daromad olish imkoniyatiga ega bo‘lasiz.

🌟 <b>Aksiya narxi:</b> <i>5 000 soʻm <s>12 000 so‘m</s></i>

🎁 <b>Bonus tizimi:</b>

Do‘stingiz botga /start bosganda, <b>+20 RC</b> hisobingizga avtomatik qo‘shiladi.

Do‘stingiz referal paketni  sotib olsa, <b>+5 000 so‘m</b> bonus hisobingizga qo‘shiladi.

<b>⚠️ Muhim:</b> <i>Barcha bonuslar avtomatik tarzda tizim tomonidan hisoblanadi.</i>

👤 <b>Admin:</b> @lok_for_me

⏳ <b>Aksiya cheklangan vaqt uchun amal qiladi!</b>
"""
    await message.answer(
        text,
        reply_markup=referal_kb(),
        parse_mode=ParseMode.HTML
    )

#BOT HAQDA
@dp.message(F.text == "ℹ️ Bot haqida")
async def bot_haqida(message: Message):

    uid = message.from_user.id

    if not await check_access(uid):
        return

    text = """
<b>BOT MAQSADI:</b>

<b>REFERAL BOZORI</b> — bu Telegram asosidagi interaktiv moliyaviy platforma bo‘lib, foydalanuvchilarga Coin Market, o‘yin mexanizmlari va referal tizimi orqali real daromad qilish imkonini beradi.

 <b>Platforma imkoniyatlari:</b>

• Coin Market orqali RC yig‘ish
• O‘yinlar orqali RC’ni ko‘paytirish
• Erkin bozor tizimi orqali savdo qilish
• Referal havola orqali passiv daromad olish
• Kunlik bonus tizimi
• Promokod orqali maxsus mukofotlar
• Reyting va faol foydalanuvchilar uchun sovg‘alar

<b>Daromad mexanizmi qanday ishlaydi?</b>

• Har kuni tizimdan bepul bonus oling
• Do‘stlaringizni taklif qilib RC va pul ishlang
• Referal xaridlaridan qo‘shimcha daromad oling
• RC Coinlaringizni haqiqiy pulga aylantiring

<b>Nima uchun aynan REFERAL BOZORI?</b>

• Oddiy va tushunarli tizim
• Faollikka asoslangan daromad
• Doimiy yangilanib boruvchi funksiyalar
• Kuchli va shaffof hisob-kitob tizimi

🔐 <b>Xavfsizlik:</b>

<i>Barcha hisob-kitob jarayonlari nazorat qilinadi va xavfsiz amalga oshiriladi.</i>

📢 <b>Rasmiy kanal:</b> @Referal_bozori
👤 <b>Admin:</b> @referal_bozori_admin

🤝 <b>Savollar va hamkorlik uchun admin bilan bog‘laning.</b>
"""
    await message.answer(text, parse_mode="HTML")

############## BONUS OLISH ############

@dp.message(F.text == "🎁 Bonus olish")
async def bonus(message: Message):

    uid = message.from_user.id

    if not await check_access(uid):
        return

    users.setdefault(uid, {
        "sub": False,
        "phone": False,
        "rc_balance": 0,
        "money_balance": 0,
        "last_bonus": None,
        "referrer": None,
        "referrals": [],
        "reward_given": False
    })

    # Darhol bonus berish
    users[uid]["rc_balance"] += BONUS_RC
    users[uid]["money_balance"] += BONUS_SUM
    users[uid]["last_bonus"] = datetime.datetime.now()

    await message.answer(
        f"🎉 <b>Bonus berildi:</b>\n\n"
        f"💸 <b>{BONUS_SUM} so‘m</b>\n"
        f"🪙 <b>{BONUS_RC} RC</b>",
        parse_mode="HTML"  # Endi hech qanday tugma qo‘shilmaydi
    )

# ================= BALANS =================

@dp.message(F.text == "💰 Balans")
async def balans(message: Message):

    uid = message.from_user.id

    if not await check_access(uid):
        return

    users.setdefault(uid, {
    "sub": False,
    "phone": False,
    "rc_balance": 0,
    "money_balance": 0,
    "last_bonus": None,
    "referrer": None,
    "referrals": [],
    "reward_given": False
})

    rc_balance = users[uid]["rc_balance"]
    money_balance = users[uid]["money_balance"]

    formatted_rc = format_rc(rc_balance)
    formatted_money = format_money(money_balance)

    text = f"""
💼 <b>Sizning balansingiz:</b>

🪙 RC Balans: <b>{formatted_rc} RC</b>
💸 So‘m Balans: <b>{formatted_money} so‘m</b>
"""

    await message.answer(
        text,
        parse_mode="HTML"
    )

# ================= ADMIN BROADCAST =================

@dp.message(F.text.startswith("/all "))
async def send_all(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/all ", "", 1)

    success = 0
    failed = 0

    for uid in list(users.keys()):
        try:
            await bot.send_message(uid, text)
            success += 1
        except:
            failed += 1

    await message.answer(
        f"✅ Yuborildi!"
    )


@dp.message(F.text.startswith("/user "))
async def send_one(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split(" ", 2)

        if len(parts) < 3:
            raise ValueError

        user_id = int(parts[1])
        text = parts[2]

        await bot.send_message(user_id, text)

        await message.answer("✅ Yuborildi!")

    except:
        await message.answer(
            "❌ Format noto‘g‘ri!"
        )

# ================= ADMIN BONUS =================

@dp.message(F.text.startswith("/bonus "))
async def give_bonus(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()

    # ----------- BARCHAGA -----------

    if len(parts) == 2:
        value = parts[1].lower()

        if value.endswith("rc"):
            amount = float(value.replace("rc", ""))

            for uid in users:
                users[uid]["rc_balance"] += amount
                try:
                    await bot.send_message(
                        uid,
                        f"🎁 Sizga {amount} RC bonus berildi!"
                    )
                except:
                    pass

            await message.answer(
                f"🎁 Barcha userlarga {amount} RC berildi!"
            )
            return

        if value.endswith("som"):
            amount = int(value.replace("som", ""))

            for uid in users:
                users[uid]["money_balance"] += amount
                try:
                    await bot.send_message(
                        uid,
                        f"🎁 Sizga {amount} so‘m bonus berildi!"
                    )
                except:
                    pass

            await message.answer(
                f"🎁 Barcha userlarga {amount} so‘m berildi!"
            )
            return

        await message.answer("❌ Format noto‘g‘ri!")
        return

    # ----------- BITTA USERGA -----------

    if len(parts) == 3:
        try:
            user_id = int(parts[1])
            value = parts[2].lower()

            if user_id not in users:
                await message.answer("❌ User topilmadi!")
                return

            if value.endswith("rc"):
                amount = float(value.replace("rc", ""))
                users[user_id]["rc_balance"] += amount
                await bot.send_message(
                    user_id,
                    f"🎁 Sizga {amount} RC bonus berildi!"
                )
                await message.answer(
                    f"🎁 {amount} RC berildi!"
                )
                return

            if value.endswith("som"):
                amount = int(value.replace("som", ""))
                users[user_id]["money_balance"] += amount
                await bot.send_message(
                    user_id,
                    f"🎁 Sizga {amount} so‘m bonus berildi!"
                )
                await message.answer(
                    f"🎁 {amount} so‘m berildi!"
                )
                return

        except:
            await message.answer("❌ Format xato!")
            return

    await message.answer("❌ Format noto‘g‘ri!")

######

@dp.message(F.text.startswith("/link "))
async def give_link(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(message.text.split()[1])

        link = f"https://t.me/referal_bozori_bot?start={user_id}"

        await bot.send_message(
            user_id,
            f"🔗 Sizning referal linkingiz:\n\n{link}\n\n"
            f"👥 Odam taklif qiling va 50 RC oling!"
        )

        # referal orqali kirgan bo‘lsa bonus berish
        referrer = users[user_id].get("referrer")

        if referrer and not users[user_id]["reward_given"]:

            users[referrer]["rc_balance"] += 50
            users[user_id]["reward_given"] = True

            await bot.send_message(
                referrer,
                "🎉 Siz taklif qilgan odam aktiv bo‘ldi!\n"
                "+50 RC berildi!"
            )

        await message.answer("✅ Link yuborildi")

    except:
        await message.answer("❌ Xato format\n/link USER_ID")



# ================= ORQAGA =================

@dp.message(F.text.in_(["🏠 Asosiy menyu"]))
async def back_to_main(message: Message):

    uid = message.from_user.id

    if not await check_access(uid):
        return

    await message.answer(
        "📋 Asosiy menyu:",
        reply_markup=main_menu(uid)
    )

# ================= RUN =================

async def main():
    print("✅ Bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())