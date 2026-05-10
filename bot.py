import requests
import time
import os
import json
import subprocess
import threading

TOKEN = "8738323399:AAEisCBZay6ChA7ghLCfbyt7syG_KxT2AGw"
ADMIN_ID = 7939923484
SECURITY_CODE = "200712"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None
locked = True
upload_mode = False

DB_FILE = "db.json"

# =========================
# 💾 DATABASE
# =========================
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

apps = load_db()
processes = {}

# =========================
# 📡 SEND MESSAGE
# =========================
def send(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )

# =========================
# ⚙️ RUN SCRIPT (SYNC)
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
# 🔄 BACKGROUND RUN (REAL PROCESS)
# =========================
def run_background(name, path, chat_id):
    process = subprocess.Popen(
        ["python3", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    processes[name] = {
        "process": process,
        "chat_id": chat_id
    }

    apps[name] = {
        "path": path,
        "pid": process.pid,
        "status": "running"
    }

    save_db(apps)

    send(chat_id, f"🔄 {name} running PID {process.pid}")

    # =========================
    # 🌙 WATCHER (sleep detection)
    # =========================
    def watcher():
        process.wait()
        send(chat_id, f"🌙 {name} stopped / sleeping 😴")
        if name in apps:
            apps[name]["status"] = "stopped"
            save_db(apps)

    threading.Thread(target=watcher, daemon=True).start()

# =========================
# 🗑️ DELETE (REAL KILL)
# =========================
def delete_app(name):
    if name in processes:
        try:
            p = processes[name]["process"]
            p.terminate()
            p.kill()
            del processes[name]
        except:
            pass

    if name in apps:
        del apps[name]
        save_db(apps)
        return True

    return False

# =========================
# 🔄 UPDATES
# =========================
def get_updates():
    global last_update_id

    url = BASE_URL + "/getUpdates"
    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    return requests.get(url).json()

# =========================
# 🚀 BOOT
# =========================
def boot():
    send(ADMIN_ID,
         "🟢 LUVY STACK ENGINE ONLINE\n"
         "━━━━━━━━━━━━━━\n"
         "System: Awake 🔓\n"
         "Deploy: Active 🚀\n"
         "Process Manager: Running ⚙️"
    )

boot()

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
                    send(chat_id, "🔓 SYSTEM UNLOCKED 🚀")
                else:
                    send(chat_id, "System locked 🔒")
                continue

            # =========================
            # 📤 UPLOAD
            # =========================
            if text == "/upload":
                upload_mode = True
                send(chat_id, "Send Python code 📤")
                continue

            if upload_mode:
                os.makedirs("deploy", exist_ok=True)

                path = "deploy/uploaded.py"
                with open(path, "w") as f:
                    f.write(text)

                upload_mode = False
                send(chat_id, "Uploaded 🚀 Use /runbg name uploaded.py")
                continue

            # =========================
            # 🚀 RUN BG
            # =========================
            if text.startswith("/runbg"):
                parts = text.split()

                if len(parts) < 3:
                    send(chat_id, "Usage: /runbg name file.py")
                    continue

                name = parts[1]
                file = parts[2]
                path = f"deploy/{file}"

                run_background(name, path, chat_id)

            # =========================
            # 🗑️ DELETE
            # =========================
            elif text.startswith("/delete"):
                name = text.split()[1]

                if delete_app(name):
                    send(chat_id, f"🗑️ {name} fully stopped")
                else:
                    send(chat_id, "Not found ❌")

            # =========================
            # 📊 DASHBOARD
            # =========================
            elif text == "/dashboard":
                if not apps:
                    send(chat_id, "No apps running")
                else:
                    msg_out = "\n".join([
                        f"{k} → PID {v['pid']} ({v['status']})"
                        for k, v in apps.items()
                    ])

                    send(chat_id, "📊 DASHBOARD\n" + msg_out)

            elif text == "/ping":
                send(chat_id, "pong 🟢")

            elif text == "/lock":
                locked = True
                send(chat_id, "System locked 🔒")

            else:
                send(chat_id,
                     "/upload\n/runbg\n/delete\n/dashboard\n/ping")

    time.sleep(2)