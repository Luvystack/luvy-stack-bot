import requests
import time

TOKEN = "8738323399:AAEisCBZay6ChA7ghLCfbyt7syG_KxT2AGw"
ADMIN_ID = 7939923484

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None
locked = True


def send(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )


def get_updates():
    global last_update_id

    url = BASE_URL + "/getUpdates"
    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    return requests.get(url).json()


while True:
    data = get_updates()

    if "result" in data:
        for update in data["result"]:
            last_update_id = update["update_id"]

            if "message" not in update:
                continue

            msg = update["message"]
            chat_id = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            text = msg.get("text", "")

            # 🔐 ADMIN CHECK
            if user_id != ADMIN_ID:
                send(chat_id, "Access denied 🚫")
                continue

            # 🔒 LOCK SYSTEM
            if locked:
                if text == "/start":
                    send(chat_id, "Enter security code 🔐")
                elif text == "200712":
                    locked = False
                    send(chat_id, "System unlocked 🔓 Welcome sir")
                    send(chat_id, "All systems running ⚙️")
                else:
                    send(chat_id, "System locked. Send /start")
                continue

            # ⚙️ COMMANDS (UNLOCKED STATE)
            if text == "/ping":
                send(chat_id, "pong 🟢")

            elif text == "/status":
                send(chat_id, "System running 24/7 ☁️")

            elif text == "/lock":
                locked = True
                send(chat_id, "System locked 🔒")

            else:
                send(chat_id, "Commands: /ping /status /lock")

    time.sleep(2)