# ================= IMPORTS =================
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import random
import sqlite3

# ================= CONFIG =================
TOKEN = "8509483715:AAGvkw4l615yb4VZTlQHsE9LEyvruyYn3iM"
ADMIN_ID = 7161801865   # <-- /myid se jo aaya tha wahi number
UPI_ID = "mdnau61@oksbi"

# ================= DATABASE =================
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT
)
""")
conn.commit()

# ================= UTIL =================
def calculate_payout(amount: int):
    payout_map = {
        20: 35,
        50: 90,
        100: 190,
        200: 380,
        500: 950
    }
    payout = payout_map.get(amount)
    if payout is None:
        return None, None
    admin_profit = amount * 2 - payout
    return payout, admin_profit


# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 Welcome to Ludo Game Bot\n\n"
        "/play 50  - Play match\n"
        "/rules    - Game rules\n"
        "/result 100 - Submit result\n"
        "/myid     - Check your Telegram ID"
    )

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 RULES:\n"
        "1. Coin bahar = loss\n"
        "2. Screenshot compulsory\n"
        "3. Network issue = no refund\n"
        "4. Admin decision final"
    )

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Your Telegram ID is: {update.effective_user.id}"
    )


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /play 20")
        return

    amount = int(context.args[0])

    allowed_amounts = [20, 50, 100, 200, 500]
    if amount not in allowed_amounts:
        await update.message.reply_text(
            "❌ Invalid amount\nAllowed: 20, 50, 100, 200, 500"
        )
        return

    match_id = f"LUDO{random.randint(1000,9999)}"

    cursor.execute(
        "INSERT INTO matches VALUES (?, ?, ?, ?)",
        (match_id, update.effective_user.id, amount, "pending")
    )
    conn.commit()

    await update.message.reply_text(
        f"🎮 Match Created\n\n"
        f"🆔 Match ID: {match_id}\n"
        f"💰 Entry Fee: ₹{amount}\n\n"
        f"📌 Pay UPI: {UPI_ID}\n"
        f"📸 Send screenshot after payment"
    )


async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Screenshot received\n"
        "⏳ Admin verification pending"
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized")
        return

    await update.message.reply_text(
        "✅ Payment approved\n"
        "🎮 You can play the match now"
    )

async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /result <amount>\nExample: /result 100"
        )
        return

    amount = int(context.args[0])

    # FRAUD CHECK
    cursor.execute(
        "SELECT status FROM matches WHERE user_id = ? AND status = 'completed'",
        (update.effective_user.id,)
    )
    if cursor.fetchone():
        await update.message.reply_text("❌ You already submitted result")
        return

    payout, admin_profit = calculate_payout(amount)
    if payout is None:
        await update.message.reply_text("❌ Invalid amount")
        return

    cursor.execute(
        "UPDATE matches SET status = 'completed' WHERE user_id = ? AND amount = ?",
        (update.effective_user.id, amount)
    )
    conn.commit()

    await update.message.reply_text(
        f"🏆 RESULT CONFIRMED\n\n"
        f"💰 Entry: ₹{amount}\n"
        f"✅ Winner Gets: ₹{payout}\n"
        f"🧾 Admin Profit: ₹{admin_profit}\n\n"
        f"📌 Payout manually via UPI"
    )

# ================= MAIN =================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("result", result))
    app.add_handler(MessageHandler(filters.PHOTO, screenshot))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

