# ================= IMPORTLAR =================

from aiogram import Router, F
from aiogram.types import Message
import os
from dotenv import load_dotenv
from keyboards import admin_main_kb, admin_back_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ================= CONFIGURATION =================

load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
router = Router()

# ================= FUNKSIYA =================

def is_admin(user_id: int):
    return user_id == ADMIN_ID

# ================= STATE CLASS =================

class LinkState(StatesGroup):
    waiting_user_id = State()

# ================= ADMIN MAIN =================

@router.message(F.text == "👨‍💻 ADMIN PANELI")
async def admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "👨‍💻 ADMIN PANELI:",
        reply_markup=admin_main_kb()
    )

# ================= ADMIN PANELIGA QAYTISH =================

@router.message(F.text == "⬅️ Admin paneli")
async def back_to_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "👨‍💻 ADMIN PANELI:",
        reply_markup=admin_main_kb()
    )

# ================= LINK BERISH =================

@router.message(F.text == "🔗 Link berish")
async def link_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🔗 Link berish bo‘limi\n\n👤 User ID yuboring:",
        reply_markup=admin_main_kb()
    )
    await state.set_state(LinkState.waiting_user_id)

# ================= STATISTIKA =================

@router.message(F.text == "📊 Statistika")
async def stat_handler(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📊 Statistika bo‘limi",
        reply_markup=admin_back_kb()
    )

# ================= BONUS =================

@router.message(F.text == "🎁 Bonuslar nazorati")
async def bonus_handler(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = """
<b>🎁 Bonuslar nazorati bo‘limi:</b>

👤SOʻM: /bonus ID 100som
👤RC: /bonus ID 100rc
👥 SOʻM: /bonus 100som
👥 RC: /bonus 100rc
"""
    await message.answer(
        text,
        reply_markup=admin_back_kb(),
        parse_mode="HTML"
    )

# ================= XABAR =================

@router.message(F.text == "📢 Xabar yuborish")
async def xabar_handler(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = """
<b>📢 Xabar yuborish bo‘limi:</b>

👤: /user ID text
👥: /all text
"""
    await message.answer(
        text,
        reply_markup=admin_back_kb(),
        parse_mode="HTML"
    )

# ================= ADMIN BONUS BERISH =================

@router.message(F.text.startswith("/bonus "))
async def give_bonus(message: Message):
    if not is_admin(message.from_user.id):
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
                    await bot.send_message(uid, f"🎁 Sizga {amount} RC bonus berildi!")
                except:
                    pass
            await message.answer(f"🎁 Barcha userlarga {amount} RC berildi!")
            return
        if value.endswith("som"):
            amount = int(value.replace("som", ""))
            for uid in users:
                users[uid]["money_balance"] += amount
                try:
                    await bot.send_message(uid, f"🎁 Sizga {amount} so‘m bonus berildi!")
                except:
                    pass
            await message.answer(f"🎁 Barcha userlarga {amount} so‘m berildi!")
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
                await bot.send_message(user_id, f"🎁 Sizga {amount} RC bonus berildi!")
                await message.answer(f"🎁 {amount} RC berildi!")
                return
            if value.endswith("som"):
                amount = int(value.replace("som", ""))
                users[user_id]["money_balance"] += amount
                await bot.send_message(user_id, f"🎁 Sizga {amount} so‘m bonus berildi!")
                await message.answer(f"🎁 {amount} so‘m berildi!")
                return
        except:
            await message.answer("❌ Format xato!")
            return

    await message.answer("❌ Format noto‘g‘ri!")

# ================= LINK YUBORISH =================

@router.message(F.text.startswith("/link "))
async def give_link(message: Message):
    if not is_admin(message.from_user.id):
        return

    try:
        user_id = int(message.text.split()[1])
        link = f"https://t.me/referal_bozori_bot?start={user_id}"
        await bot.send_message(
            user_id,
            f"🔗 Sizning referal linkingiz:\n\n{link}\n\n👥 Odam taklif qiling va 50 RC oling!"
        )

        referrer = users[user_id].get("referrer")
        if referrer and not users[user_id]["reward_given"]:
            users[referrer]["rc_balance"] += 50
            users[user_id]["reward_given"] = True
            await bot.send_message(referrer, "🎉 Siz taklif qilgan odam aktiv bo‘ldi!\n+50 RC berildi!")

        await message.answer("✅ Link yuborildi")

    except:
        await message.answer("❌ Xato format\n/link USER_ID")