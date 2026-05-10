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

# 🧠 system state
system_alive = True


# =========================
# 🔔 TELEGRAM SENDER
# =========================
def send(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )


# =========================
# ⚙️ RUN SCRIPT (foreground)
# =========================
def run_script(filename):
    try:
        path = f"deploy/{filename}"
        result = subprocess.check_output(
            ["python3", path],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30
        )
        return result if result else "Executed (no output)"
    except Exception as e:
        return str(e)


# =========================
# 🔄 BACKGROUND SERVICE RUNNER
# =========================
def run_background(path):
    def target():
        try:
            exec(open(path).read(), {})
        except Exception as e:
            print("BG ERROR:", e)

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()


# =========================
# 🔁 HEARTBEAT SYSTEM
# =========================
def heartbeat():
    global system_alive
    while True:
        system_alive = True
        time.sleep(10)


threading.Thread(target=heartbeat, daemon=True).start()


# =========================
# 🚀 ON START MESSAGE (WAKE UP)
# =========================
def system_boot_message():
    try:
        msg = (
            "🟢 Luvy Stack System Online\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔓 Status: Awake\n"
            "⚙️ Engine: Running Stable\n"
            "📡 Mode: Cloud Execution Active\n"
            "🔄 Ready: Accepting Deployments\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "Send /start to unlock system."
        )
        # broadcast to admin only (you can expand later)
        requests.post(
            BASE_URL + "/sendMessage",
            data={"chat_id": ADMIN_ID, "text": msg}
        )
    except:
        pass


system_boot_message()


# =========================
# 🔄 TELEGRAM POLLING
# =========================
def get_updates():
    global last_update_id

    url = BASE_URL + "/getUpdates"
    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    return requests.get(url).json()


# =========================
# 🧠 MAIN LOOP
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

            # 🔐 ADMIN ONLY
            if user_id != ADMIN_ID:
                send(chat_id, "Access denied 🚫")
                continue

            # 🔒 LOCK SYSTEM
            if locked:
                if text == "/start":
                    send(chat_id, "🔐 Enter security code to unlock system")
                elif text == SECURITY_CODE:
                    locked = False

                    send(chat_id,
                         "🔓 SYSTEM UNLOCKED\n"
                         "━━━━━━━━━━━━━━\n"
                         "Welcome back sir.\n"
                         "All systems are now active ⚙️\n"
                         "Monitoring services enabled 📡\n"
                         "Deploy engine ready 🚀"
                    )
                else:
                    send(chat_id, "System locked. Use /start")
                continue

            # ⚙️ DEPLOY SYSTEM
            if text.startswith("/deploy"):
                parts = text.split()

                if len(parts) < 2:
                    send(chat_id, "Usage: /deploy filename.py")
                    continue

                filename = parts[1]
                output = run_script(filename)

                send(chat_id, f"📦 Output:\n{output}")

            # 🔄 BACKGROUND SERVICE
            elif text.startswith("/runbg"):
                parts = text.split()

                if len(parts) < 2:
                    send(chat_id, "Usage: /runbg filename.py")
                    continue

                filename = parts[1]
                path = f"deploy/{filename}"

                run_background(path)

                send(chat_id, f"🔄 Background service started: {filename}")

            # 📡 STATUS
            elif text == "/status":
                send(chat_id,
                     "🟢 SYSTEM STATUS REPORT\n"
                     "━━━━━━━━━━━━━━━━━━\n"
                     "Engine: Running\n"
                     "Deploy: Active\n"
                     "Background Services: Enabled\n"
                     "Memory: Stable\n"
                     "Mode: Cloud Runtime\n"
                     "━━━━━━━━━━━━━━━━━━"
                )

            # 🔒 LOCK
            elif text == "/lock":
                locked = True
                send(chat_id, "System locked 🔒")

            # 🟢 PING
            elif text == "/ping":
                send(chat_id, "pong 🟢")

            else:
                send(chat_id,
                     "Commands:\n"
                     "/deploy file.py\n"
                     "/runbg file.py\n"
                     "/status\n"
                     "/lock"
                )

    time.sleep(2)