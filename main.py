from aiogram import Bot
from aiogram.enums import ParseMode
from keyboards import coin_market_kb
import random
import datetime
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from keyboards import clicker_inline_kb
from storage import users, clicker_stats, clicker_state


##########

mini_game_state = {}  # Foydalanuvchi holati

# ================= FORMAT FUNCTIONS =================

def format_rc(amount: float) -> str:
    text = f"{amount:.4f}"
    return text.rstrip("0").rstrip(".")

MAX_DAILY_RC = 100.0

router = Router()

######

def get_clicker_ranking():
    return sorted(
        clicker_stats.items(),
        key=lambda x: x[1]["total_rc"],
        reverse=True
    )

# Inline tugma

def mini_game_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏱️ To‘xtatish", callback_data="stop_timer")]
        ]
    )
   
#coin market

@router.message(F.text == "🪙 Coin Market")
async def coin_market(message: Message):

    text = """
<b>Coin Market orqali siz:</b>

• Bepul <b>RC</b> tangalarini yig‘ishingiz
• <b>O‘yin</b> va <b>lotereyalar</b> orqali balansni ko‘paytirishingiz
• Valyuta statistikalarini tahlil qilishingiz
• Bozordagi narx harakatlarini kuzatib, tangalaringizni qulay vaqtda sotishingiz
• Yig‘ilgan <b>RC</b>ʻlarni haqiqiy pulga aylantirishingiz mumkin.

<i>📈 Aqlli savdo qiling, to‘g‘ri vaqtni tanlang va daromadingizni oshiring!</i>
"""

    await message.answer(
        text,
        reply_markup=coin_market_kb(),
        parse_mode=ParseMode.HTML
    )


#COIN MARKETGA QAYTISH

@router.message(F.text == "⬅️ Coin Market")
async def back_to_coin(message: Message):

    await message.answer(
        "🪙 Coin Market:",
        reply_markup=coin_market_kb()
    )
# ================= START =================

@router.message(F.text == "🕹 RC yig‘ish")
async def start_clicker(message: Message):
    uid = message.from_user.id

    state = clicker_state.setdefault(uid, {
    "click_count": 0,
    "pause_until": None,
    "daily_rc": 0.0,
    "daily_reset": datetime.date.today(),
})

    now = datetime.datetime.now()

    if state["daily_reset"] != now.date():
        state.update({
            "click_count": 0,
            "pause_until": None,
            "daily_rc": 0.0,
            "daily_reset": now.date(),
        })

    text = (
        f"<b>🪙 REFERAL COIN – CLICKER</b>\n\n"
        f"💰 UMUMIY BALANS: <b>{format_rc(users[uid]['rc_balance'])} RC</b>\n"
f"⏱️ Bugun yig‘ilgan: <code>{format_rc(state['daily_rc'])} / {format_rc(MAX_DAILY_RC)}</code>\n\n"
        f"🎉 Joriy hisob: +0 RC"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=clicker_inline_kb())

# ================= CLICK =================

@router.callback_query(F.data == "click_coin")
async def click_coin(call: CallbackQuery):
    uid = call.from_user.id
    now = datetime.datetime.now()

    state = clicker_state.setdefault(uid, {
        "click_count": 0,
        "pause_until": None,
        "daily_rc": 0.0,
        "daily_reset": datetime.date.today(),
    })

    # 📅 Daily reset
    if state["daily_reset"] != now.date():
        state.update({
            "click_count": 0,
            "pause_until": None,
            "daily_rc": 0.0,
            "daily_reset": now.date(),
        })

    # ⏳ Pause tekshiruv
    if state["pause_until"] and now < state["pause_until"]:
        remaining = int((state["pause_until"] - now).total_seconds())
        await call.answer(f"⏳ {remaining} soniya kuting", show_alert=True)
        return

    # 🎲 Random RC (balanslangan)
    rc = round(random.uniform(0.0050, 0.0150), 4)

    # 🚫 Daily limit
    if state["daily_rc"] + rc > MAX_DAILY_RC:
        await call.answer("🚫 Kunlik limit tugadi!", show_alert=True)
        return

    # 💰 Balans qo‘shish
    users[uid]["rc_balance"] += rc
    state["daily_rc"] += rc
    state["click_count"] += 1

# CLICKER REYTING STAT
    if uid not in clicker_stats:
        clicker_stats[uid] = {
            "total_rc": 0
        }

    clicker_stats[uid]["total_rc"] += rc

    # ⏳ 50 urishdan keyin pause
    if state["click_count"] >= 50:
        state["pause_until"] = now + datetime.timedelta(seconds=15)
        state["click_count"] = 0

    text = (
        f"<b>🪙 REFERAL COIN – CLICKER</b>\n\n"
        f"💰 UMUMIY BALANS: <b>{format_rc(users[uid]['rc_balance'])} RC</b>\n"
        f"⏱️ Bugun yig‘ilgan: <code>{format_rc(state['daily_rc'])} / {format_rc(MAX_DAILY_RC)}</code>\n\n"
        f"🎉 Joriy hisob: +{format_rc(rc)} RC"
    )

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=clicker_inline_kb())

###############################

# 🏆 Reyting
@router.message(F.text == "🏆 Reyting")
async def clicker_ranking(message: Message, bot: Bot):

    ranking = get_clicker_ranking()

    text = "🏆 RC YIG‘ISH REYTING\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for position, (user_id, data) in enumerate(ranking[:10], start=1):
        try:
            user = await bot.get_chat(user_id)
            username = user.username or user.first_name
        except:
            username = "user"

        medal = medals[position-1] if position <= 3 else f"{position}"

        text += (
            f"{medal} @{username} "
            f"{format_rc(data['total_rc'])} RC\n"
        )

    await message.answer(text)

#########

# ------------------- MINI O'YIN (00:00:00 - 00:15:00) -------------------

@router.message(F.text == "🎯 Mini O‘yin")
async def start_mini_game(message: Message):
    uid = message.from_user.id
    now = datetime.datetime.now()

    # O‘yin boshlanish va tugash vaqti
    start_time = datetime.time(0, 0, 0)
    end_time = datetime.time(0, 15, 0)
    target_time = datetime.time(0, 10, 0)  # Maqsad

    mini_game_state[uid] = {
        "start": start_time,
        "end": end_time,
        "target": target_time,
        "reward_given": False,
        "started_at": now
    }

    await message.answer(
        "🎯 Mini o‘yinga xush kelibsiz!\n\n"
        "🔹 Maqsad: 00:10:00 vaqtga yaqin to‘xtatish.\n"
        "⏱️ Inline tugma orqali to‘xtating va agar to‘g‘ri vaqtni ushlasangiz 50 RC olasiz!\n"
        "🕒 O‘yin 00:00:00 dan 00:15:00 gacha davom etadi.",
        reply_markup=mini_game_kb()
    )

@router.callback_query(F.data == "stop_timer")
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

    # 1 soniya farq ruxsat
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
        await call.answer("❌ Xato vaqt, afsus! Qayta urinib ko‘ring.", show_alert=True)

    # Tugmani olib tashlash va o‘yin holatini tozalash
    await call.message.edit_reply_markup(reply_markup=None)
    mini_game_state.pop(uid, None)
