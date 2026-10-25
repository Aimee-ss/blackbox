
import math
import random
import sqlite3
import threading
import webbrowser

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Local demonstration only. Use synthetic data, not real company secrets.
# The unauthenticated admin endpoint exposes mock raw rows.
# Never expose this prototype to a network or use it in production.


def init_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row

    with conn:
        conn.execute(
            "CREATE TABLE shared_telemetry ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "company_owner TEXT NOT NULL, "
            "build_duration_sec REAL NOT NULL, "
            "active_bugs INTEGER NOT NULL, "
            "proprietary_patch_key TEXT NOT NULL)"
        )

        conn.executemany(
            "INSERT INTO shared_telemetry "
            "(company_owner, build_duration_sec, active_bugs, "
            "proprietary_patch_key) VALUES (?, ?, ?, ?)",
            [
                ("Company_A", 42.5, 12, "PATCH_SECURE_A88X"),
                ("Company_A", 48.1, 8, "PATCH_SECURE_A12B"),
                ("Company_B", 55.4, 24, "KEY_ENCRYPT_B991"),
                ("Company_B", 51.9, 19, "KEY_ENCRYPT_B443"),
            ],
        )

    return conn


db_conn = init_db()
db_lock = threading.Lock()
budget_lock = threading.Lock()

privacy_budgets = {"A": 2.00, "B": 2.00}
QUERY_COSTS = {"safe": 0.10, "attack": 1.50}


def generate_laplace_noise(scale):
    # Illustrative only; this is not a complete differential
    # privacy implementation.
    if scale <= 0:
        return 0.0

    u = random.random() - 0.5
    return (
        -scale
        * math.copysign(1.0, u)
        * math.log1p(-2.0 * abs(u))
    )


@app.route("/", methods=["GET"])
def render_frontend():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def handle_query():
    payload = request.get_json(silent=True) or {}
    tenant = payload.get("tenant")
    query_mode = payload.get("mode")

    if tenant not in privacy_budgets or query_mode not in QUERY_COSTS:
        return jsonify({
            "status": "ERROR",
            "log": "Invalid tenant or query mode.",
        }), 400

    query_cost = QUERY_COSTS[query_mode]

    with budget_lock:
        if privacy_budgets[tenant] < query_cost:
            return jsonify({
                "status": "REJECTED",
                "log": "Privacy budget is insufficient for this demo query.",
                "remaining_budget": privacy_budgets[tenant],
            }), 200

        privacy_budgets[tenant] = round(
            privacy_budgets[tenant] - query_cost, 2
        )
        remaining_budget = privacy_budgets[tenant]

    if query_mode == "safe":
        # Return a noisy aggregate rather than individual rows.
        with db_lock:
            row = db_conn.execute(
                "SELECT AVG(build_duration_sec) AS avg_duration "
                "FROM shared_telemetry"
            ).fetchone()

            raw_average = float(row["avg_duration"])

        noise = generate_laplace_noise(scale=0.5)
        protected_average = max(0.0, raw_average + noise)

        output = (
            "Approximate fleet average build duration: "
            f"{protected_average:.2f} seconds"
        )

        logs = [
            "Authorized aggregate query accepted.",
            "Database returned an aggregate, not individual rows.",
            f"[DP ENGINE] Illustrative noise sample: {noise:.5f}",
            "Only the approximate aggregate was returned to the tenant.",
        ]
        status = "APPROVED"

    else:
        # Never query the other company's proprietary key.
        output = (
            "Request denied. Private company records are not "
            "available through this query."
        )

        logs = [
            "[ACCESS CONTROL] Private-record access attempt rejected.",
            "No proprietary patch key was queried or returned.",
        ]
        status = "REJECTED"

    return jsonify({
        "status": status,
        "remaining_budget": remaining_budget,
        "output": output,
        "logs": logs,
    })


@app.route("/api/admin/view-db", methods=["GET"])
def admin_view_db():
    # DEMO ONLY: unauthenticated raw-data endpoint.
    # Do not expose publicly.
    with db_lock:
        rows = db_conn.execute(
            "SELECT id, company_owner, build_duration_sec, "
            "active_bugs, proprietary_patch_key "
            "FROM shared_telemetry ORDER BY id"
        ).fetchall()

    return jsonify({
        "database_rows": [dict(row) for row in rows]
    })


@app.route("/api/reset", methods=["POST"])
def handle_reset():
    with budget_lock:
        privacy_budgets.update({"A": 2.00, "B": 2.00})

    return jsonify({"status": "RESET_SUCCESS"})


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5050/")


if __name__ == "__main__":
    print("=" * 60)
    print("BLACK BOX AI — LOCAL SOFTWARE TELEMETRY PROTOTYPE")
    print("Dashboard: http://127.0.0.1:5050/")
    print("Synthetic data only; this is not production-secure.")
    print("=" * 60)

    threading.Timer(1.0, open_browser).start()
    app.run(host="127.0.0.1", port=5050, debug=False)
