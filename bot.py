import requests
import time
import os
import json
import threading
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


# =========================
# 📡 SEND MESSAGE (SAFE)
# =========================
def send(chat_id, text):
    try:
        requests.post(
            BASE_URL + "/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except:
        print("Send error")


# =========================
# ⚙️ RUN SCRIPT (FIXED)
# =========================
def run_script(path):
    if not os.path.exists(path):
        return "❌ File not found"

    try:
        result = subprocess.check_output(
            ["python3", path],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30
        )
        return result if result else "Executed"

    except subprocess.CalledProcessError as e:
        return f"❌ Python Error:\n{e.output}"

    except Exception as e:
        return str(e)


# =========================
# 🔄 BACKGROUND SERVICE
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

    apps[name] = {"path": path, "status": "running"}
    save_db(apps)


# =========================
# 🗑️ DELETE APP
# =========================
def delete_app(name):
    if name in apps:
        del apps[name]
        save_db(apps)
        return True
    return False


# =========================
# 🔄 UPDATES (SAFE)
# =========================
def get_updates():
    global last_update_id

    try:
        url = BASE_URL + "/getUpdates"
        if last_update_id:
            url += f"?offset={last_update_id + 1}"

        return requests.get(url, timeout=10).json()
    except:
        return {"result": []}


# =========================
# 🚀 BOOT MESSAGE
# =========================
def boot():
    send(ADMIN_ID,
         "🟢 LUWY STACK ONLINE\n"
         "━━━━━━━━━━━━━━\n"
         "System: Awake 🔓\n"
         "Engine: Running ⚙️\n"
         "Deploy: Active 🚀\n"
         "Database: Loaded 💾"
    )


boot()


# =========================
# 🧠 MAIN LOOP (STABLE)
# =========================
while True:
    try:
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
                             "All systems active ⚙️\n"
                             "Ready for deployment 🚀"
                        )
                    else:
                        send(chat_id, "System locked. Use /start")
                    continue

                # =========================
                # 📤 UPLOAD SYSTEM
                # =========================
                if text == "/upload":
                    upload_mode = True
                    send(chat_id, "Send Python code now 📤")
                    continue

                if upload_mode:
                    os.makedirs("deploy", exist_ok=True)

                    path = os.path.join("deploy", "uploaded.py")

                    with open(path, "w") as f:
                        f.write(text)

                    upload_mode = False
                    send(chat_id, "Uploaded 🚀 Use /deploy uploaded.py")
                    continue

                # =========================
                # 🚀 DEPLOY APP
                # =========================
                if text.startswith("/deploy"):
                    parts = text.split()
                    if len(parts) < 3:
                        send(chat_id, "Usage: /deploy name file.py")
                        continue

                    name = parts[1]
                    file = parts[2]

                    path = os.path.join("deploy", file)

                    output = run_script(path)

                    apps[name] = {"path": path, "status": "deployed"}
                    save_db(apps)

                    send(chat_id, f"📦 {name} deployed\n\n{output}")

                # =========================
                # 🔄 BACKGROUND RUN
                # =========================
                elif text.startswith("/runbg"):
                    parts = text.split()
                    if len(parts) < 3:
                        send(chat_id, "Usage: /runbg name file.py")
                        continue

                    name = parts[1]
                    file = parts[2]

                    path = os.path.join("deploy", file)

                    run_background(name, path)

                    send(chat_id, f"🔄 {name} running in background")

                # =========================
                # 🗑️ DELETE APP
                # =========================
                elif text.startswith("/delete"):
                    parts = text.split()
                    if len(parts) < 2:
                        send(chat_id, "Usage: /delete name")
                        continue

                    name = parts[1]

                    if delete_app(name):
                        send(chat_id, f"🗑️ {name} deleted")
                    else:
                        send(chat_id, "Not found ❌")

                # =========================
                # 📊 DASHBOARD
                # =========================
                elif text == "/dashboard":
                    if not apps:
                        apps_list = "No apps running"
                    else:
                        apps_list = "\n".join(
                            [f"• {k} → {v['status']}" for k, v in apps.items()]
                        )

                    send(chat_id,
                         "📊 LUWY DASHBOARD\n"
                         "━━━━━━━━━━━━━━\n"
                         f"{apps_list}\n"
                         "━━━━━━━━━━━━━━\n"
                         "System Active 🟢"
                    )

                elif text == "/status":
                    send(chat_id, "System running ☁️")

                elif text == "/ping":
                    send(chat_id, "pong 🟢")

                elif text == "/lock":
                    locked = True
                    send(chat_id, "System locked 🔒")

                else:
                    send(chat_id,
                         "Commands:\n"
                         "/upload\n"
                         "/deploy name file.py\n"
                         "/runbg name file.py\n"
                         "/delete name\n"
                         "/dashboard")

    except Exception as e:
        print("Main loop error:", e)
        time.sleep(2)