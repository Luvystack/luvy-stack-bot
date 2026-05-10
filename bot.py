import requests
import time
import subprocess

TOKEN = "8738323399:AAEisCBZay6ChA7ghLCfbyt7syG_KxT2AGw"
ADMIN_ID = 7939923484
SECURITY_CODE = "200712"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None
state = "LOCKED"


def send_message(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )


def run_script(filename):
    try:
        result = subprocess.check_output(
            ["python", f"/data/data/com.termux/files/home/deploy/{filename}"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20
        )
        return result
    except Exception as e:
        return str(e)


def get_updates():
    global last_update_id

    url = BASE_URL + "/getUpdates"
    if last_update_id is not None:
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

            # 🔐 ADMIN ONLY
            if user_id != ADMIN_ID:
                send_message(chat_id, "Access denied 🚫")
                continue

            # 🔒 LOCK SYSTEM
            if state == "LOCKED":
                if text == "/start":
                    state = "WAITING_CODE"
                    send_message(chat_id, "Provide system security code 🔐")
                else:
                    send_message(chat_id, "System locked. Use /start")

            elif state == "WAITING_CODE":
                if text == SECURITY_CODE:
                    state = "UNLOCKED"
                    send_message(chat_id, "System unlocked 🔓 Welcome sir")
                    send_message(chat_id, "All systems running ⚙️")
                else:
                    send_message(chat_id, "Wrong code ❌")

            elif state == "UNLOCKED":

                # 🔥 DEPLOY SYSTEM
                if text.startswith("/deploy"):
                    parts = text.split()

                    if len(parts) < 2:
                        send_message(chat_id, "Usage: /deploy filename.py")
                        continue

                    filename = parts[1]
                    output = run_script(filename)

                    send_message(chat_id, f"📦 Deploy result:\n{output}")

                elif text == "/status":
                    send_message(chat_id, "All systems running ⚙️")

                elif text == "/lock":
                    state = "LOCKED"
                    send_message(chat_id, "System locked 🔒")

                elif text == "/ping":
                    send_message(chat_id, "pong 🟢")

                else:
                    send_message(chat_id, "Commands: /deploy /status /lock")

    time.sleep(2)