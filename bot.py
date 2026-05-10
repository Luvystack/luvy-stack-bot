import requests
import time
import os
import threading
import subprocess

TOKEN = "8738323399:AAEisCBZay6ChA7ghLCfbyt7syG_KxT2AGw"
ADMIN_ID = 7939923484
SECURITY_CODE = "200712"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None
locked = True

# 📦 registry of running apps
apps_registry = {}


# =========================
# SEND MESSAGE
# =========================
def send(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )


# =========================
# RUN SCRIPT (foreground)
# =========================
def run_script(path):
    try:
        result = subprocess.check_output(
            ["python3", path],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30
        )
        return result if result else "Executed"
    except Exception as e:
        return str(e)


# =========================
# BACKGROUND RUNNER
# =========================
def run_background(name, path):
    def target():
        try:
            exec(open(path).read(), {})
        except Exception as e:
            print(f"[{name}] ERROR:", e)

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()

    apps_registry[name] = {
        "path": path,
        "status": "running",
        "thread": thread
    }


# =========================
# DELETE APP
# =========================
def delete_app(name):
    if name in apps_registry:
        del apps_registry[name]
        return True
    return False


# =========================
# TELEGRAM POLLING
# =========================
def get_updates():
    global last_update_id

    url = BASE_URL + "/getUpdates"
    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    return requests.get(url).json()


# =========================
# MAIN LOOP
# =========================
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
                    send(chat_id,
                         "🔓 SYSTEM UNLOCKED\n"
                         "Deploy engine active 🚀\n"
                         "Multi-app system ready ⚙️"
                    )
                else:
                    send(chat_id, "System locked. Use /start")
                continue

            # =========================
            # 🚀 DEPLOY NAMED APP
            # =========================
            if text.startswith("/deploy"):
                parts = text.split()

                if len(parts) < 3:
                    send(chat_id, "Usage: /deploy appname file.py")
                    continue

                name = parts[1]
                file = parts[2]
                path = f"deploy/{file}"

                result = run_script(path)

                apps_registry[name] = {
                    "path": path,
                    "status": "deployed"
                }

                send(chat_id, f"📦 App '{name}' deployed\n\n{result}")

            # =========================
            # 🔄 RUN BACKGROUND APP
            # =========================
            elif text.startswith("/runbg"):
                parts = text.split()

                if len(parts) < 3:
                    send(chat_id, "Usage: /runbg appname file.py")
                    continue

                name = parts[1]
                file = parts[2]
                path = f"deploy/{file}"

                run_background(name, path)

                send(chat_id, f"🔄 App '{name}' running in background")

            # =========================
            # 🗑️ DELETE APP
            # =========================
            elif text.startswith("/delete"):
                parts = text.split()

                if len(parts) < 2:
                    send(chat_id, "Usage: /delete appname")
                    continue

                name = parts[1]

                if delete_app(name):
                    send(chat_id, f"🗑️ App '{name}' deleted")
                else:
                    send(chat_id, "App not found ❌")

            # =========================
            # 📡 STATUS
            # =========================
            elif text == "/status":
                send(chat_id,
                     "🟢 SYSTEM STATUS\n"
                     f"Apps running: {len(apps_registry)}\n"
                     "Engine: Active\n"
                     "Multi-App: Enabled"
                )

            # =========================
            elif text == "/ping":
                send(chat_id, "pong 🟢")

            elif text == "/lock":
                locked = True
                send(chat_id, "System locked 🔒")

            else:
                send(chat_id,
                     "Commands:\n"
                     "/deploy name file.py\n"
                     "/runbg name file.py\n"
                     "/delete name\n"
                     "/status"
                )

    time.sleep(2)