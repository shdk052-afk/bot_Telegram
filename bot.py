from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8632809247:AAE3EY11-dKok1cCn0_35GFgzcIFayu0O9A"

# תפריט ראשי
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📊 מידע", callback_data="info")],
        [InlineKeyboardButton("❓ עזרה", callback_data="help")],
        [InlineKeyboardButton("🎮 משחק", callback_data="game")]
    ]
    return InlineKeyboardMarkup(keyboard)

# פקודת start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "שלום! אני הבוט של שחר 😎\nבחר אופציה:",
        reply_markup=get_main_menu()
    )

# טיפול בלחיצות
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "info":
        await query.edit_message_text("זה בוט מגניב 😎", reply_markup=get_main_menu())

    elif query.data == "help":
        await query.edit_message_text("איך אפשר לעזור? 🤔", reply_markup=get_main_menu())

    elif query.data == "game":
        await query.edit_message_text("בוא נשחק 🎮 (נוסיף משחק בהמשך 😈)", reply_markup=get_main_menu())

# הרצת הבוט
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()