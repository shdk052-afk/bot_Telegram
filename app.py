from flask import Flask, request
import requests

app = Flask(__name__)

TOKEN = "8632809247:AAE3EY11-dKok1cCn0_35GFgzcIFayu0O9A"
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_menu(chat_id)
        else:
            send_message(chat_id, f"קיבלתי: {text}")

    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        data_pressed = data["callback_query"]["data"]

        send_message(chat_id, f"לחצת על: {data_pressed}")

    return "ok"


def send_menu(chat_id):
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "כפתור 1", "callback_data": "btn1"},
                {"text": "כפתור 2", "callback_data": "btn2"}
            ],
            [
                {"text": "על הבוט", "callback_data": "about"}
            ]
        ]
    }

    requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": "בחר אופציה:",
        "reply_markup": keyboard
    })


def send_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
