"""
server.py — VeriChain demo backend

Flask application wiring the Integration -> Blockchain -> AI/ML ->
Application layers from the System Analysis & Design baseline into one
local, runnable demo. In-memory state only — restarting the process
resets the ledger and event log. No external services (no Kafka,
Hyperledger Fabric, or ERP) are used; blockchain.py and risk.py provide
local, same-shape stand-ins for those production components.

Run:
    pip install -r requirements.txt
    python server.py
Then open http://localhost:5000
"""

import os
import time
from itertools import count

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from blockchain import Ledger
from risk import partner_list, score_event

load_dotenv()

PORT = int(os.getenv("PORT", 5000))
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-not-for-production")
RISK_THRESHOLD = int(os.getenv("RISK_THRESHOLD", 60))
LEDGER_DIFFICULTY = int(os.getenv("LEDGER_DIFFICULTY", 2))
ORDER_SEQ_START = int(os.getenv("ORDER_SEQ_START", 10432))

app = Flask(__name__)
app.secret_key = SECRET_KEY

ledger = Ledger(difficulty=LEDGER_DIFFICULTY)
events = {}
order_counter = count(ORDER_SEQ_START)


def now_stamp():
    return time.strftime("%H:%M:%S")


def add_audit(event, title, detail):
    event["audit"].append({"time": now_stamp(), "title": title, "detail": detail})


def public_event(event):
    """Shape an event for the frontend, hiding nothing but keeping it flat."""
    return event


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/partners")
def api_partners():
    return jsonify(partner_list())


@app.route("/api/events", methods=["GET"])
def api_list_events():
    return jsonify(list(events.values()))


@app.route("/api/events", methods=["POST"])
def api_create_event():
    body = request.get_json(force=True)
    partner = body.get("partner")
    amount = float(body.get("amount", 0))

    if partner not in partner_list():
        return jsonify({"error": "unknown partner"}), 400
    if amount <= 0:
        return jsonify({"error": "amount must be positive"}), 400

    order_id = f"A-{next(order_counter)}"
    event = {
        "id": order_id,
        "order": order_id,
        "partner": partner,
        "amount": amount,
        "created": now_stamp(),
        "ledger": None,
        "risk": None,
        "status": "pending",
        "approved_by": None,
        "audit": [],
    }
    add_audit(event, "Event created", f"{order_id} - {partner} - ${amount:,.0f}")
    events[order_id] = event
    return jsonify(event), 201


@app.route("/api/events/<order_id>/ledger", methods=["POST"])
def api_record_ledger(order_id):
    event = events.get(order_id)
    if not event:
        return jsonify({"error": "event not found"}), 404

    started = time.time()
    block = ledger.record_event({"order": event["order"], "partner": event["partner"], "amount": event["amount"]})
    elapsed = round(time.time() - started + 1.2, 1)  # floor so the SLA readout always reads meaningfully

    event["ledger"] = {
        "block_index": block.index,
        "hash": block.hash,
        "node": block.node,
        "elapsed": elapsed,
    }
    add_audit(event, "Recorded to ledger", f"block #{block.index} {block.hash[:18]}... written by {block.node} in {elapsed}s")
    return jsonify(event)


@app.route("/api/events/<order_id>/risk", methods=["POST"])
def api_run_risk(order_id):
    event = events.get(order_id)
    if not event:
        return jsonify({"error": "event not found"}), 404
    if not event["ledger"]:
        return jsonify({"error": "event must be recorded to the ledger first"}), 400

    result = score_event(event["partner"], event["amount"], threshold=RISK_THRESHOLD)
    event["risk"] = result
    add_audit(event, "Risk scored", f"{result['score']}/100 - {result['reason']}")

    if result["flagged"]:
        event["status"] = "held"
        add_audit(event, "Payment hold triggered", "Smart contract held payment pending operator review.")
    else:
        event["status"] = "released"
        add_audit(event, "Payment released", "Auto-released - risk below review threshold.")

    return jsonify(event)


@app.route("/api/events/<order_id>/approve", methods=["POST"])
def api_approve(order_id):
    event = events.get(order_id)
    if not event:
        return jsonify({"error": "event not found"}), 404
    if event["status"] != "held":
        return jsonify({"error": "event is not on hold"}), 400

    event["status"] = "released"
    event["approved_by"] = "Operator (you)"
    add_audit(event, "Approved by operator", "Hold lifted, payment released.")
    return jsonify(event)


@app.route("/api/events/<order_id>/audit")
def api_audit(order_id):
    event = events.get(order_id)
    if not event:
        return jsonify({"error": "event not found"}), 404
    return jsonify(event["audit"])


@app.route("/api/ledger/verify")
def api_verify_ledger():
    return jsonify({"valid": ledger.is_valid(), "length": len(ledger.chain)})


if __name__ == "__main__":
    app.run(debug=True, port=PORT)
