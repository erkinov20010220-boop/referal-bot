import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ================== SOZLAMALAR ==================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL = "@referal_bozori"

REF_TARGET = 10
REF_REWARD = 15000

# ================== DATABASE ==================
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    referrer INTEGER,
    refs INTEGER DEFAULT 0,
    balance INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS withdraws(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT
)
""")
conn.commit()

# ================== MENU ==================
menu = ReplyKeyboardMarkup(
    [
        ["🔗 Referal link", "📊 Statistika"],
        ["💰 Balans", "📤 Pul yechish"],
        ["💳 Click", "👤 Admin"]
    ],
    resize_keyboard=True
)

# ================== KANAL TEKSHIRISH ==================
async def check_sub(bot, user_id):
    try:
        m = await bot.get_chat_member(CHANNEL, user_id)
        return m.status in ("member", "administrator", "creator")
    except:
        return False

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot = context.bot

    # Kanalga obuna tekshirish
    if not await check_sub(bot, uid):
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Kanalga obuna bo‘lish", url=f"https://t.me/{CHANNEL[1:]}")]
        ])
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun kanalga obuna bo‘ling",
            reply_markup=kb
        )
        return

    # Foydalanuvchi bazada bormi
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not cur.fetchone():
        ref = None
        if context.args:
            try:
                r = int(context.args[0])
                if r != uid:
                    ref = r
            except:
                pass

        cur.execute(
            "INSERT INTO users(user_id, referrer) VALUES(?, ?)",
            (uid, ref)
        )

        if ref:
            cur.execute("UPDATE users SET refs = refs + 1 WHERE user_id=?", (ref,))
            cur.execute("SELECT refs FROM users WHERE user_id=?", (ref,))
            refs = cur.fetchone()[0]
            if refs >= REF_TARGET:
                cur.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id=?",
                    (REF_REWARD, ref)
                )

        conn.commit()

    await update.message.reply_text(
        "👋 Xush kelibsiz!\n\n"
        "💸 10 ta referal = 15 000 so‘m\n"
        "📢 Referal linkingizni ulashing",
        reply_markup=menu
    )

# ================== REFERAL LINK ==================
async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot = await context.bot.get_me()
    await update.message.reply_text(
        f"🔗 Sizning referal linkingiz:\n"
        f"https://t.me/{bot.username}?start={uid}"
    )

# ================== STATISTIKA ==================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur.execute("SELECT refs, balance FROM users WHERE user_id=?", (uid,))
    r, b = cur.fetchone()
    await update.message.reply_text(
        f"📊 Referallar soni: {r}\n"
        f"💰 Balans: {b} so‘m"
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Statistika":
        await stats(update, context)

    elif text == "💰 Balans":
        await balance(update, context)

    elif text == "📤 Pul yechish":
        await withdraw(update, context)

    elif text == "🔗 Referal link":
        await link(update, context)

    elif text == "💳 Click":
        await click(update, context)

    elif text == "👤 Admin":
        await admin(update, context)

# ================== BALANS ==================
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    b = cur.fetchone()[0]
    await update.message.reply_text(f"💰 Balansingiz: {b} so‘m")

# ================== PUL YECHISH ==================
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cur.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    b = cur.fetchone()[0]

    if b < REF_REWARD:
        await update.message.reply_text("❌ Minimal yechish: 15 000 so‘m")
        return

    cur.execute(
        "INSERT INTO withdraws(user_id, amount, status) VALUES(?,?,?)",
        (uid, b, "pending")
    )
    cur.execute("UPDATE users SET balance=0 WHERE user_id=?", (uid,))
    conn.commit()

    await update.message.reply_text("📨 So‘rov yuborildi. Admin bilan bog‘laning.")
    await context.bot.send_message(
        ADMIN_ID,
        f"📤 Yangi pul yechish so‘rovi\nUser ID: {uid}\nSumma: {b} so‘m"
    )

# ================== CLICK ==================
async def click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Click (TEST)", callback_data="click_test")]
    ])
    await update.message.reply_text("💳 To‘lov usulini tanlang:", reply_markup=kb)

async def click_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("🧪 Click TEST tanlandi.\nAdmin bilan bog‘laning.")
    await context.bot.send_message(
        ADMIN_ID,
        f"💳 Click TEST bosildi\nUser ID: {q.from_user.id}"
    )

# ================== ADMIN ==================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Admin: @Lok_for_me")

# ================== RUN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("click", click))
    app.add_handler(CallbackQueryHandler(click_cb, pattern="click_test"))
    app.add_handler(CommandHandler("admin", admin))

    app.run_polling()

if __name__ == "__main__":
    main()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))