import requests
import time
import os

TOKEN = "8738323399:AAEisCBZay6ChA7ghLCfbyt7syG_KxT2AGw"
ADMIN_ID = 7939923484
SECURITY_CODE = "200712"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None
locked = True
upload_mode = False


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


def run_script(filename):
    try:
        path = f"deploy/{filename}"
        result = os.popen(f"python3 {path}").read()
        return result if result else "Executed (no output)"
    except Exception as e:
        return str(e)


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
                elif text == SECURITY_CODE:
                    locked = False
                    send(chat_id, "System unlocked 🔓 Welcome sir")
                    send(chat_id, "All systems running ⚙️")
                else:
                    send(chat_id, "System locked. Use /start")
                continue

            # 📤 UPLOAD SYSTEM
            if text == "/upload":
                upload_mode = True
                send(chat_id, "Send your Python code now 📤")
                continue

            if upload_mode:
                os.makedirs("deploy", exist_ok=True)

                file_path = "deploy/uploaded.py"
                with open(file_path, "w") as f:
                    f.write(text)

                upload_mode = False
                send(chat_id, "File uploaded 🚀 Use /deploy uploaded.py")
                continue

            # ⚙️ COMMANDS
            if text.startswith("/deploy"):
                parts = text.split()

                if len(parts) < 2:
                    send(chat_id, "Usage: /deploy filename.py")
                    continue

                filename = parts[1]
                output = run_script(filename)

                send(chat_id, f"📦 Output:\n{output}")

            elif text == "/ping":
                send(chat_id, "pong 🟢")

            elif text == "/status":
                send(chat_id, "System running ☁️")

            elif text == "/lock":
                locked = True
                send(chat_id, "System locked 🔒")

            else:
                send(chat_id, "Commands: /upload /deploy /ping /status /lock")

    time.sleep(2)