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
# SETUP FOLDERS
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

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(apps, f, indent=2)

apps = load_db()

# =========================
# TELEGRAM HELPERS
# =========================
def send(chat_id, text):
    try:
        requests.post(
            BASE_URL + "/sendMessage",
            data={"chat_id": chat_id, "text": text},
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
# SAFETY CHECK
# =========================
def scan_code(code):
    blocked = [
        "rm -rf",
        "fork",
        "kill",
        "shutdown",
        "os.system"
    ]

    for b in blocked:
        if b in code:
            return False, f"Blocked keyword: {b}"

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
        return f"❌ BLOCKED\n{reason}"

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
    except Exception as e:
        return f"❌ SAVE ERROR\n{e}"

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

    save_db()

    return f"🚀 DEPLOYED: {name}"

# =========================
# STOP APP
# =========================
def stop_app(name):
    if name not in apps:
        return "❌ Not found"

    try:
        os.killpg(os.getpgid(apps[name]["pid"]), signal.SIGTERM)
        apps[name]["status"] = "stopped"
        save_db()
        return f"🛑 Stopped: {name}"
    except Exception as e:
        return f"❌ STOP ERROR\n{e}"

# =========================
# LOGS
# =========================
def get_logs(name):
    if name not in apps:
        return "❌ App not found"

    try:
        with open(apps[name]["log"], "r") as f:
            return f.read()[-3000:]
    except:
        return "No logs"

# =========================
# DASHBOARD
# =========================
def dashboard():
    if not apps:
        return "📦 No apps running"

    text = "📦 LUVY STACK DASHBOARD\n━━━━━━━━━━━━━━\n"
    for k, v in apps.items():
        text += f"• {k} → {v['status']}\n"
    return text

# =========================
# STATE
# =========================
last_update_id = 0
pending_code = {}

print("⚡ LUVY STACK ENGINE RUNNING")

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

# =========================
# MAIN LOOP (STRICT FLOW)
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

            # only admin
            if user_id != ADMIN_ID:
                continue

            # =========================
            # START
            # =========================
            if text == "/start":
                send(chat_id, MENU)
                continue

            # =========================
            # DEPLOY INIT
            # =========================
            if text.startswith("/deploy "):
                name = text.split(" ", 1)[1].strip()
                pending_code[user_id] = name
                send(chat_id, f"📥 Send code for: {name}")
                continue

            # =========================
            # CODE INPUT
            # =========================
            if user_id in pending_code:
                name = pending_code.pop(user_id)
                send(chat_id, deploy_app(name, text))
                continue

            # =========================
            # APPS
            # =========================
            if text == "/apps":
                send(chat_id, dashboard())
                continue

            # =========================
            # DASHBOARD
            # =========================
            if text == "/dashboard":
                send(chat_id, dashboard())
                continue

            # =========================
            # LOGS
            # =========================
            if text.startswith("/logs"):
                parts = text.split()
                send(chat_id, get_logs(parts[1]) if len(parts) > 1 else "Usage: /logs name")
                continue

            # =========================
            # STOP
            # =========================
            if text.startswith("/stop"):
                parts = text.split()
                send(chat_id, stop_app(parts[1]) if len(parts) > 1 else "Usage: /stop name")
                continue

            # =========================
            # PING
            # =========================
            if text == "/ping":
                send(chat_id, "pong 🟢")
                continue

    except Exception as e:
        print("ERROR:", e)

    time.sleep(2)