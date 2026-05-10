import requests
import time
import os
import json
import subprocess

TOKEN = "8738323399:AAEisCBZay6ChA7ghLCfbyt7syG_KxT2AGw"
ADMIN_ID = 7939923484
SECURITY_CODE = "200712"

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = None
locked = True
upload_mode = False

DB_FILE = "db.json"

# =========================
# STORAGE
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
# TELEGRAM SEND
# =========================
def send(chat_id, text):
    requests.post(
        BASE_URL + "/sendMessage",
        data={"chat_id": chat_id, "text": text}
    )

# =========================
# START PROCESS
# =========================
def run_background(name, path):
    process = subprocess.Popen(
        ["python3", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    processes[name] = process

    apps[name] = {
        "path": path,
        "pid": process.pid,
        "status": "running"
    }

    save_db(apps)

# =========================
# STOP / DELETE PROCESS
# =========================
def delete_app(name):
    if name in apps:
        try:
            if name in processes:
                processes[name].terminate()
                processes[name].kill()
                del processes[name]

            del apps[name]
            save_db(apps)
            return True
        except:
            return False
    return False

# =========================
# LIVE LOGS
# =========================
def get_logs(name):
    if name not in processes:
        return "No process"

    p = processes[name]

    try:
        output = p.stdout.readline()
        if output:
            return output.strip()
        return "No logs yet"
    except:
        return "Log error"

# =========================
# UPDATES
# =========================
def get_updates():
    global last_update_id

    url = BASE_URL + "/getUpdates"
    if last_update_id:
        url += f"?offset={last_update_id + 1}"

    return requests.get(url).json()

# =========================
# BOOT
# =========================
def boot():
    send(ADMIN_ID,
         "🟢 LUWY STACK ENGINE ONLINE\n"
         "━━━━━━━━━━━━━━\n"
         "System: Awake 🔓\n"
         "Deploy: Active 🚀\n"
         "Process Manager: Running ⚙️"
    )

boot()

# =========================
# LOOP
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

            # ADMIN ONLY
            if user_id != ADMIN_ID:
                send(chat_id, "Access denied 🚫")
                continue

            # LOCK SYSTEM
            if locked:
                if text == "/start":
                    send(chat_id, "Enter security code 🔐")
                elif text == SECURITY_CODE:
                    locked = False
                    send(chat_id, "🔓 SYSTEM UNLOCKED")
                else:
                    send(chat_id, "Locked 🔒")
                continue

            # UPLOAD
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

            # RUN BACKGROUND
            if text.startswith("/runbg"):
                parts = text.split()
                name = parts[1]
                file = parts[2]

                path = f"deploy/{file}"
                run_background(name, path)

                send(chat_id, f"🔄 {name} running PID {apps[name]['pid']}")

            # DELETE (FULL KILL)
            elif text.startswith("/delete"):
                name = text.split()[1]

                if delete_app(name):
                    send(chat_id, f"🗑️ {name} stopped completely")
                else:
                    send(chat_id, "Not found ❌")

            # DASHBOARD
            elif text == "/dashboard":
                if not apps:
                    send(chat_id, "No apps running")
                else:
                    msg_out = "\n".join([
                        f"{k} → PID {v['pid']} ({v['status']})"
                        for k, v in apps.items()
                    ])

                    send(chat_id, "📊 DASHBOARD\n" + msg_out)

            # LOGS
            elif text.startswith("/logs"):
                name = text.split()[1]
                send(chat_id, get_logs(name))

            elif text == "/ping":
                send(chat_id, "pong 🟢")

            elif text == "/lock":
                locked = True
                send(chat_id, "System locked 🔒")

            else:
                send(chat_id,
                     "/upload\n"
                     "/runbg name file.py\n"
                     "/delete name\n"
                     "/dashboard\n"
                     "/logs name")

    time.sleep(2)