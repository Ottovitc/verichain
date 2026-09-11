# VeriChain — Demo

A local, runnable demo of the VeriChain architecture signed off in the System Analysis &
Design baseline: a permissioned ledger, a fraud risk engine, and an operator console, wired
together behind a small Flask API. No external services required — everything runs on your
machine.

## Requirements

- Python 3.9+
- pip

## Setup

```bash
cd verichain-demo
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configure (optional)

Defaults live in `.env` and are read automatically — edit values there if you want to change
the port, risk threshold, ledger proof-of-work difficulty, or starting order number.

| Variable | Default | Meaning |
|---|---|---|
| `PORT` | `5000` | Local server port |
| `FLASK_SECRET_KEY` | `dev-secret-not-for-production` | Flask session secret |
| `RISK_THRESHOLD` | `60` | Score at/above which a payment is held for review |
| `LEDGER_DIFFICULTY` | `2` | Leading zeros required in a block hash (proof-of-work) |
| `ORDER_SEQ_START` | `10432` | First order number issued |

## Run

```bash
python server.py
```

Open **http://localhost:5000** in a browser.

## Walking through the demo

1. **New Event** — pick a partner and a payment amount, click **Create Event**.
2. **Record to Ledger** — mines and appends a real SHA-256 block (with proof-of-work) to the
   in-memory chain; shows the hash, the writing node, and elapsed time.
3. **Run Risk Check** — scores the payment against that partner's typical order size; high
   ratios flag the event and hold the payment automatically.
4. Flagged events appear in the **Operator Queue** — click **Approve & Release** to clear the
   hold.
5. Once released, click **Export Audit Record** to see the full timeline for that event.

Restarting `server.py` resets the ledger and all events — state is in-memory only, by design,
so the demo always starts clean.

## Project layout

```
verichain-demo/
├── server.py           Flask app and API routes
├── blockchain.py        Hash-chained ledger (Block, Ledger, proof-of-work)
├── risk.py               Fraud risk scoring + fictional partner data
├── templates/
│   └── index.html        Frontend UI
├── requirements.txt
├── .env                   Local configuration
└── README.md
```

## Notes

- The ledger and risk engine are local stand-ins for the production Hyperledger Fabric ledger
  and the trained scikit-learn/XGBoost model described in the SAD report — same shape and API
  contract, real hashing and chain-validity logic, no external network.
- `GET /api/ledger/verify` walks the whole chain and confirms hash/proof-of-work integrity —
  useful to demonstrate tamper-evidence live.
