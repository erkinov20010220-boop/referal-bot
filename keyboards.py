from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ================= COIN MARKET ================= 

def coin_market_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🕹 RC yig‘ish"),
             KeyboardButton(text="🎲 Mini Oʻyin")],
            [KeyboardButton(text="🏆 Reyting")],
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True
    )

################# Toʻxtatish #############

def mini_game_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎯 To‘xtat va Bonus ol",  # Takomillashtirilgan nom
                    callback_data="stop_timer"
                )
            ]
        ]
    )

# ================= REFERAL =================

def referal_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True
    )


# ================= PUL YECHISH =================

def pul_yechish_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Karta kiritish")],
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True
    )

# ================= ADMIN PANEL =================

def admin_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔗 Link berish")],
            [KeyboardButton(text="🎁 Bonuslar nazorati"),
             KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True
    )

def admin_back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Admin paneli")]
        ],
        resize_keyboard=True
    )