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

# ================= DATABASE =================
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

    # ใช้ ENV แทน hardcode
    c.execute("INSERT OR IGNORE INTO admin VALUES (1, ?)", (ADMIN_PASSWORD,))

    conn.commit()
    conn.close()

# ================= KEY SYSTEM =================
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
    c.execute("INSERT INTO keys VALUES (?,?,?,?)",
              (key, None, None, "active"))
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
    return (time.time() - start_time) > 86400

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
.title { font-size:22px; text-shadow:0 0 10px #00ffcc; }

.card {
    background:#111;
    border:1px solid #00ffcc33;
    border-radius:10px;
    padding:15px;
    margin-bottom:20px;
}

button {
    background:#00ffcc;
    border:none;
    padding:6px 12px;
    border-radius:6px;
    cursor:pointer;
    font-weight:bold;
}

.del { background:red; color:white; }
.reset { background:orange; color:black; }
.copy { background:#0077ff; color:white; }

table { width:100%; border-collapse:collapse; }
th, td { border:1px solid #00ffcc33; padding:8px; text-align:center; }
</style>
</head>

<body>

<div class="header">
    <div class="title">Dashboard - Slash HUB</div>
    <a href="/logout"><button>logout</button></a>
</div>

<div class="card">
Total Keys: {{ total }} | Active: {{ active }}
</div>

<div class="card">
<form action="/generate">
<input name="amount" value="1">
<button>generate</button>
</form>
</div>

<div class="card">
<table>
<tr>
<th>KEY</th>
<th>HWID</th>
<th>START</th>
<th>ACTION</th>
</tr>

{% for k,v in KEYS.items() %}
<tr>
<td>{{k}}</td>
<td>{{v["hwid"] or "-"}}</td>
<td>{{v["start_time"] or "-"}}</td>
<td>
<button class="copy" onclick="navigator.clipboard.writeText('{{k}}')">copy</button>
<a href="/reset?key={{k}}"><button class="reset">reset</button></a>
<a href="/delete?key={{k}}"><button class="del">del</button></a>
</td>
</tr>
{% endfor %}

</table>
</div>

</body>
</html>
"""

LOGIN = """
<form method="post">
<input name="password" placeholder="admin">
<button>LOGIN</button>
</form>
"""

# ================= ROUTES =================
@app.route("/login", methods=["GET","POST"])
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
    total = len(data)
    active = sum(1 for v in data.values() if v["hwid"] is not None)

    return render_template_string(DASH, KEYS=data, total=total, active=active)


@app.route("/generate")
def generate():
    if not login_required():
        return "no access"

    amount = int(request.args.get("amount",1))

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
    return redirect("/dashboard")

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

    return redirect("/dashboard")

# ================= CHECK API =================
@app.route("/check")
def check():
    key = request.args.get("key")
    hwid = request.args.get("hwid")

    if not key or not hwid:
        return "invalid"

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "invalid"

    data = {
        "hwid": row[1],
        "start_time": row[2],
        "status": row[3]
    }

    if data["hwid"] is None:
        conn = db()
        c = conn.cursor()
        c.execute("UPDATE keys SET hwid=?, start_time=? WHERE key=?",
                  (hwid, time.time(), key))
        conn.commit()
        conn.close()
        return "binded"

    if data["hwid"] != hwid:
        return "hwid_error"

    if is_expired(data["start_time"]):
        return "expired"

    return "ok"

@app.route("/script")
def script():
    key = request.args.get("key")
    if not key:
        return "print('no key')"

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        conn.close()
        return "print('invalid key')"

    # HWID bind แบบเดียวกับ check
    hwid = request.headers.get("User-Agent")

    if row[1] is None:
        c.execute("UPDATE keys SET hwid=?, start_time=? WHERE key=?",
                  (hwid, time.time(), key))
        conn.commit()

    elif row[1] != hwid:
        conn.close()
        return "print('hwid error')"

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
