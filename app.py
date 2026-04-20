
import os

from flask import Flask, request

from bot_logic import TelegramBotLogic


app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8632809247:AAE3EY11-dKok1cCn0_35GFgzcIFayu0O9A")
bot_logic = TelegramBotLogic(token=TOKEN, workdir="tmp")


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    bot_logic.process_update(data)
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
