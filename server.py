from flask import Flask, request, jsonify, render_template_string, redirect, session
import sqlite3, time, os, secrets, random, string

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# ===== DB =====
def db():
    return sqlite3.connect("keys.db")

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        hwid TEXT,
        start_time REAL
    )
    """)
    conn.commit()
    conn.close()

# ===== UTIL =====
def gen_key():
    return "SLASH-" + "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

def is_expired(start):
    return start and (time.time() - start) > 86400

# ===== AUTH LOGIC =====
def validate(key, hwid):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    if not row:
        return "invalid"

    db_hwid, start = row[1], row[2]

    if db_hwid is None:
        c.execute("UPDATE keys SET hwid=?, start_time=? WHERE key=?",
                  (hwid, time.time(), key))
        conn.commit()
        conn.close()
        return "binded"

    if db_hwid != hwid:
        conn.close()
        return "hwid_error"

    if is_expired(start):
        conn.close()
        return "expired"

    conn.close()
    return "ok"

# ===== TOKEN =====
TOKENS = {}

def create_token(key, hwid):
    t = secrets.token_hex(16)
    TOKENS[t] = {"key": key, "hwid": hwid, "time": time.time()}
    return t

# ===== 🔥 STAGE 1 (loader) =====
@app.route("/script")
def script():
    key = request.args.get("key")
    hwid = request.headers.get("User-Agent", "unknown")

    if not key:
        return "print('no key')"

    status = validate(key, hwid)
    if status not in ["ok", "binded"]:
        return f"print('{status}')"

    # 🔐 สร้าง token (ซ่อน)
    token = create_token(key, hwid)

    base = request.host_url

    return f"""
-- hidden stage
local __t = "{token}"
local __u = "{base}stage2?token="..__t

local __s = game:HttpGet(__u)
loadstring(__s)()
"""

# ===== 🔥 STAGE 2 (ตัวจริง) =====
@app.route("/stage2")
def stage2():
    token = request.args.get("token")
    data = TOKENS.get(token)

    if not data:
        return "print('bad token')"

    if time.time() - data["time"] > 15:
        del TOKENS[token]
        return "print('expired')"

    status = validate(data["key"], data["hwid"])
    if status not in ["ok", "binded"]:
        del TOKENS[token]
        return f"print('{status}')"

    # 🔥 ใช้ครั้งเดียว
    del TOKENS[token]

    with open("real.lua", "r", encoding="utf-8") as f:
        code = f.read()

    return f"""
if not game or not game.Players then return end
task.wait(math.random())
{code}
"""

# ===== LOGIN =====
def login_required():
    return session.get("admin")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["pw"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/dash")
        return "wrong password"

    return """
    <form method='post'>
    <input name='pw' placeholder='password'>
    <button>login</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ===== DASHBOARD =====
HTML = """
<h2>⚡ Slash Dashboard</h2>
<a href='/logout'>Logout</a>

<h3>Generate Key</h3>
<form action='/gen'>
<input name='n' value='1'>
<button>Generate</button>
</form>

<h3>Keys</h3>
{% for k,v in keys.items() %}
<p>
{{k}} | HWID: {{v[0]}} | TIME: {{v[1]}}
<a href='/delete?key={{k}}'>[DEL]</a>
</p>
{% endfor %}
"""

@app.route("/dash")
def dash():
    if not login_required():
        return redirect("/login")

    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM keys")
    rows = c.fetchall()
    conn.close()

    data = {r[0]:(r[1],r[2]) for r in rows}

    return render_template_string(HTML, keys=data)

@app.route("/gen")
def gen():
    if not login_required():
        return "no access"

    n = int(request.args.get("n",1))

    conn = db()
    c = conn.cursor()

    out=[]
    for _ in range(n):
        k = gen_key()
        c.execute("INSERT INTO keys VALUES (?,?,?)",(k,None,None))
        out.append(k)

    conn.commit()
    conn.close()

    return "<br>".join(out)

@app.route("/delete")
def delete():
    if not login_required():
        return "no access"

    key = request.args.get("key")

    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM keys WHERE key=?",(key,))
    conn.commit()
    conn.close()

    return redirect("/dash")

# ===== START =====
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)