from flask import Flask, request, render_template_string, redirect, session
import sqlite3
import os
import time
import random
import string

app = Flask(__name__)

# ================= ENV =================
app.secret_key = os.environ.get("SECRET_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# ================= SECURITY =================
RATE_LIMIT = {}
IP_LOG = {}
SCRIPT_TOKENS = {}

KEY_EXPIRE = 86400  # 1 day


# ================= RATE LIMIT =================
def rate_limit(ip):
    now = time.time()
    last = RATE_LIMIT.get(ip, 0)
    if now - last < 2:
        return False
    RATE_LIMIT[ip] = now
    return True


# ================= LOG IP =================
def log_ip(ip, msg):
    IP_LOG[ip] = msg
    print(f"[IP:{ip}] {msg}")


# ================= TOKEN =================
def gen_token(key):
    token = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(24))
    SCRIPT_TOKENS[key] = {"token": token, "time": time.time()}
    return token


def verify_token(key, token):
    data = SCRIPT_TOKENS.get(key)
    if not data:
        return False
    if data["token"] != token:
        return False
    if time.time() - data["time"] > 60:
        return False
    return True


# ================= DB =================
def db():
    return sqlite3.connect("keys.db")


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        hwid TEXT,
        start_time REAL,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        password TEXT
    )
    """)

    c.execute("INSERT OR IGNORE INTO admin VALUES (1, ?)", (ADMIN_PASSWORD,))

    conn.commit()
    conn.close()


# ================= KEY =================
def get_keys():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM keys")
    rows = c.fetchall()
    conn.close()

    return {
        r[0]: {
            "hwid": r[1],
            "start_time": r[2],
            "status": r[3]
        } for r in rows
    }


def add_key(key):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO keys VALUES (?,?,?,?)", (key, None, None, "active"))
    conn.commit()
    conn.close()


def delete_key_db(key):
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM keys WHERE key=?", (key,))
    conn.commit()
    conn.close()


def is_expired(start_time):
    if start_time is None:
        return False
    return (time.time() - start_time) > KEY_EXPIRE


def get_expire_time(start_time):
    if not start_time:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time + KEY_EXPIRE))


# ================= AUTH =================
def login_required():
    return session.get("admin") == True


def gen_key():
    return "SLASH-" + "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))


# ================= UI =================
DASH = """
<!DOCTYPE html>
<html>
<head>
<title>Dashboard</title>
<meta http-equiv="refresh" content="5">
<style>
body { background:#0d0d0d; color:#00ffcc; font-family:monospace; padding:20px; }
.header { display:flex; justify-content:space-between; margin-bottom:20px; }
.card { background:#111; padding:15px; margin-bottom:20px; border-radius:10px; }
table { width:100%; border-collapse:collapse; }
th, td { border:1px solid #00ffcc33; padding:8px; text-align:center; }
button { background:#00ffcc; border:none; padding:6px; border-radius:6px; }
.del { background:red; }
.reset { background:orange; }
</style>
</head>
<body>

<div class="header">
<h2>Dashboard</h2>
<a href="/logout"><button>logout</button></a>
</div>

<div class="card">
Total Keys: {{ total }} | Active: {{ active }}
</div>

<table>
<tr>
<th>KEY</th>
<th>HWID</th>
<th>START</th>
<th>EXPIRE</th>
<th>ACTION</th>
</tr>

{% for k,v in KEYS.items() %}
<tr>
<td>{{k}}</td>
<td>{{v["hwid"] or "-"}}</td>
<td>{{v["start_time"] or "-"}}</td>
<td>{{v["expire"]}}</td>
<td>
<a href="/reset?key={{k}}"><button class="reset">reset</button></a>
<a href="/delete?key={{k}}"><button class="del">del</button></a>
</td>
</tr>
{% endfor %}

</table>

</body>
</html>
"""

LOGIN = """<form method="post"><input name="password"><button>login</button></form>"""


# ================= ROUTES =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form["password"]

        conn = db()
        c = conn.cursor()
        c.execute("SELECT password FROM admin WHERE id=1")
        real = c.fetchone()[0]
        conn.close()

        if pw == real:
            session["admin"] = True
            return redirect("/dashboard-backend")

        return "wrong"

    return LOGIN


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def home():
    return "Key Server Running"


@app.route("/dashboard-backend")
def dashboard():
    if not login_required():
        return redirect("/login")

    data = get_keys()

    for k in data:
        data[k]["expire"] = get_expire_time(data[k]["start_time"])

    total = len(data)
    active = sum(1 for v in data.values() if v["hwid"] is not None)

    return render_template_string(DASH, KEYS=data, total=total, active=active)


@app.route("/generate")
def generate():
    if not login_required():
        return "no access"

    amount = int(request.args.get("amount", 1))

    keys = []
    for _ in range(amount):
        k = gen_key()
        add_key(k)
        keys.append(k)

    return "<br>".join(keys)


@app.route("/delete")
def delete():
    if not login_required():
        return "no access"

    key = request.args.get("key")
    delete_key_db(key)
    return redirect("/dashboard-backend")


@app.route("/reset")
def reset():
    if not login_required():
        return "no access"

    key = request.args.get("key")

    conn = db()
    c = conn.cursor()
    c.execute("UPDATE keys SET hwid=NULL, start_time=NULL WHERE key=?", (key,))
    conn.commit()
    conn.close()

    return redirect("/dashboard-backend")


# ================= SCRIPT SYSTEM =================
@app.route("/script")
def script():
    key = request.args.get("key")
    hwid = request.args.get("hwid")
    token = request.args.get("token")
    ip = request.remote_addr

    if not rate_limit(ip):
        return "print('rate limit')"

    if not key or not hwid:
        return "print('invalid')"

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        conn.close()
        return "print('invalid key')"

    db_hwid = row[1]
    start_time = row[2]

    if start_time and (time.time() - start_time > KEY_EXPIRE):
        conn.close()
        return "print('expired')"

    if db_hwid is None:
        c.execute("UPDATE keys SET hwid=?, start_time=? WHERE key=?",
                  (hwid, time.time(), key))
        conn.commit()

    elif db_hwid != hwid:
        conn.close()
        log_ip(ip, "HWID BLOCKED")
        return "print('hwid locked')"

    if not token:
        token = gen_token(key)

    if not verify_token(key, token):
        conn.close()
        return "print('invalid token')"

    conn.close()

    try:
        with open("script.lua", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "print('script missing')"


# ================= START =================
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
