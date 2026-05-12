import os
import json
import time
import requests
import subprocess
import signal

# =========================
# CONFIG
# =========================
TOKEN = "8738323399:AAEisCBZay6ChA7ghLCfbyt7syG_KxT2AGw"
ADMIN_ID = 7939923484

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_FILE = "storage/apps.json"

# =========================
# FOLDERS
# =========================
os.makedirs("deploy", exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("storage", exist_ok=True)

# =========================
# DATABASE
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

# =========================
# TELEGRAM
# =========================
def send(chat_id, text):
    try:
        requests.post(
            BASE_URL + "/sendMessage",
            data={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10
        )
    except:
        pass

def get_updates(offset=None):
    try:
        url = BASE_URL + "/getUpdates"

        if offset:
            url += f"?offset={offset}"

        r = requests.get(url, timeout=20)

        return r.json()

    except:
        return {"result": []}

# =========================
# SAFETY SCANNER
# =========================
def scan_code(code):

    blocked = [
        "rm -rf",
        "fork",
        "kill",
        "shutdown",
        "reboot"
    ]

    for bad in blocked:
        if bad in code:
            return False, f"Blocked keyword: {bad}"

    try:
        compile(code, "<string>", "exec")
    except Exception as e:
        return False, str(e)

    return True, "OK"

# =========================
# DEPLOY ENGINE
# =========================
def deploy_app(name, code):

    path = f"deploy/{name}.py"
    log_path = f"logs/{name}.log"

    ok, reason = scan_code(code)

    if not ok:
        return f"❌ DEPLOY BLOCKED\n{reason}"

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

    except Exception as e:
        return f"❌ SAVE FAILED\n{e}"

    try:
        log_file = open(log_path, "a")

        process = subprocess.Popen(
            ["python3", path],
            stdout=log_file,
            stderr=log_file,
            preexec_fn=os.setsid
        )

    except Exception as e:
        return f"❌ DEPLOY FAILED\n{e}"

    apps[name] = {
        "file": path,
        "pid": process.pid,
        "log": log_path,
        "status": "running"
    }

    save_db(apps)

    return f"🚀 DEPLOYED: {name}"

# =========================
# STOP APP
# =========================
def stop_app(name):

    if name not in apps:
        return "❌ App not found"

    try:
        pid = apps[name]["pid"]

        os.killpg(
            os.getpgid(pid),
            signal.SIGTERM
        )

        apps[name]["status"] = "stopped"

        save_db(apps)

        return f"🛑 Stopped: {name}"

    except Exception as e:
        return f"❌ STOP FAILED\n{e}"

# =========================
# LOGS
# =========================
def get_logs(name):

    if name not in apps:
        return "❌ App not found"

    try:
        with open(apps[name]["log"], "r") as f:
            data = f.read()

        if not data:
            return "No logs yet"

        return data[-3500:]

    except Exception as e:
        return f"❌ LOG ERROR\n{e}"

# =========================
# DASHBOARD
# =========================
def dashboard():

    if not apps:
        return "📦 No apps deployed"

    text = "📦 LUVY STACK DASHBOARD\n"
    text += "━━━━━━━━━━━━━━\n"

    for name, app in apps.items():
        text += f"• {name} → {app['status']}\n"

    text += "━━━━━━━━━━━━━━"

    return text

# =========================
# STATES
# =========================
last_update_id = 0
pending_code = {}

# =========================
# MENU
# =========================
MENU = """
⚡ LUVY STACK ENGINE

Commands:
• /deploy name
• /apps
• /logs name
• /stop name
• /dashboard
• /ping
"""

print("⚡ LUVY STACK ENGINE ONLINE")

# =========================
# MAIN LOOP
# =========================
while True:

    try:

        updates = get_updates(last_update_id)

        for update in updates.get("result", []):

            last_update_id = update["update_id"] + 1

            msg = update.get("message")

            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            user_id = msg["from"]["id"]

            text = msg.get("text", "")

            # =========================
            # ADMIN ONLY
            # =========================
            if user_id != ADMIN_ID:
                send(chat_id, "❌ Access denied")
                continue

            # =========================
            # START
            # =========================
            if text == "/start":

                send(chat_id, MENU)
                continue

            # =========================
            # DEPLOY START
            # =========================
            elif text.startswith("/deploy "):

                name = text.split(" ", 1)[1].strip()

                if not name:
                    send(chat_id, "Usage: /deploy name")
                    continue

                pending_code[user_id] = name

                send(chat_id, f"📥 Send code for: {name}")
                continue

            # =========================
            # RECEIVE CODE
            # =========================
            elif user_id in pending_code:

                name = pending_code.pop(user_id)

                result = deploy_app(name, text)

                send(chat_id, result)
                continue

            # =========================
            # APPS
            # =========================
            elif text == "/apps":

                send(chat_id, dashboard())
                continue

            # =========================
            # DASHBOARD
            # =========================
            elif text == "/dashboard":

                send(chat_id, dashboard())
                continue

            # =========================
            # LOGS
            # =========================
            elif text.startswith("/logs"):

                parts = text.split()

                if len(parts) < 2:
                    send(chat_id, "Usage: /logs name")
                    continue

                send(chat_id, get_logs(parts[1]))
                continue

            # =========================
            # STOP
            # =========================
            elif text.startswith("/stop"):

                parts = text.split()

                if len(parts) < 2:
                    send(chat_id, "Usage: /stop name")
                    continue

                send(chat_id, stop_app(parts[1]))
                continue

            # =========================
            # PING
            # =========================
            elif text == "/ping":

                send(chat_id, "pong 🟢")
                continue

            # =========================
            # UNKNOWN
            # =========================
            else:

                send(chat_id, "❌ Unknown command")
                continue

    except Exception as e:

        print("ENGINE ERROR:", e)

    time.sleep(2)