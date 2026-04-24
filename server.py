from flask import Flask, request, render_template_string, redirect, session
import sqlite3
import os
import time
import random
import string

app = Flask(__name__)

# ================= ENV =================
app.secret_key = os.environ.get("SECRET_KEY") or "dev_secret_key"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "admin"

# ================= SECURITY =================
IP_LOG = {}
SCRIPT_TOKENS = {}
KEY_RATE = {}

KEY_EXPIRE = 86400  # 1 day

# ================= RATE LIMIT HYBRID =================
RATE_IP = {}
RATE_KEY = {}

IP_LIMIT = 2
KEY_LIMIT = 1


def rate_limit(ip, key):
    now = time.time()

    if ip and now - RATE_IP.get(ip, 0) < IP_LIMIT:
        return True

    if key and now - RATE_KEY.get(key, 0) < KEY_LIMIT:
        return True

    if ip:
        RATE_IP[ip] = now
    if key:
        RATE_KEY[key] = now

    return False


# ================= LOG =================
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
    return sqlite3.connect("keys.db", timeout=10, check_same_thread=False)


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

.header {
    display:flex;
    justify-content:space-between;
    margin-bottom:20px;
}

.card {
    background:#111;
    padding:15px;
    margin-bottom:20px;
    border-radius:10px;
}

table {
    width:100%;
    border-collapse:collapse;
}

th, td {
    border:1px solid #00ffcc33;
    padding:8px;
    text-align:center;
}

button {
    background:#00ffcc;
    border:none;
    padding:6px 10px;
    border-radius:6px;
    cursor:pointer;
    font-weight:bold;
}

.del { background:red; color:white; }
.reset { background:orange; color:black; }
.gen { background:#0077ff; color:white; }
.copy { background:#00cc88; }
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

<div class="card">
<form action="/generate">
<input name="amount" value="1" style="width:60px;">
<button class="gen">generate</button>
</form>
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
<button class="copy" onclick="navigator.clipboard.writeText('{{k}}')">copy</button>
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
        pw = request.form.get("password", "")

        conn = db()
        c = conn.cursor()
        c.execute("SELECT password FROM admin WHERE id=1")
        real = c.fetchone()
        conn.close()

        if real and pw == real[0]:
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

    out = []
    for _ in range(amount):
        k = gen_key()
        add_key(k)
        out.append(k)

    return "<br>".join(out)


@app.route("/delete")
def delete():
    if not login_required():
        return "no access"

    key = request.args.get("key")
    if key:
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


# ================= SCRIPT =================
@app.route("/script")
def script():
    key = request.args.get("key", "")
    hwid = request.args.get("hwid", "")
    ip = request.remote_addr

    if not key or not hwid:
        return "print('invalid')"

    if rate_limit(ip, key):
        return "print('rate limited')"

    conn = db()
    c = conn.cursor()

    c.execute("SELECT hwid, start_time FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        conn.close()
        return "print('invalid key')"

    db_hwid, start_time = row
    now = time.time()

    if start_time and (now - start_time > KEY_EXPIRE):
        conn.close()
        return "print('expired')"

    if db_hwid is None:
        c.execute(
            "UPDATE keys SET hwid=?, start_time=? WHERE key=?",
            (hwid, now, key)
        )
        conn.commit()

    elif db_hwid != hwid:
        conn.close()
        return "print('hwid locked')"

    conn.close()

    try:
        with open("script.lua", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "print('missing script')"


# ================= START =================
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
