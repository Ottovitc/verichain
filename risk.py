"""
risk.py — Fraud risk scoring engine

A lightweight, deterministic-ish stand-in for the ML/MLOps layer (Python,
scikit-learn, XGBoost) specified in the System Analysis & Design baseline.
It scores a payment against each partner's historical order profile and
returns a 0-100 risk score, a plain-language reason, and a flag decision —
the same contract the trained model will expose once real transaction
history is available in Implementation.
"""

import random

# Fictional partner cohort with a baseline "typical order value" (USD),
# standing in for the historical ERP data the real model will be trained on.
PARTNERS = {
    "Meridian Foods Ltd": 16000,
    "Coastal Freight Co.": 42000,
    "Northgate Retailers": 9500,
    "Savanna Agro Supplies": 21000,
    "Riftline Logistics": 33000,
    "Highland Textiles": 12500,
    "Lakeview Distributors": 27000,
    "Baraka Manufacturing": 51000,
    "Delta Cold Chain": 19500,
    "Amber Trading Group": 15000,
}

DEFAULT_BASELINE = 15000


def score_event(partner: str, amount: float, threshold: int = 60):
    """
    Score a single payment for fraud risk.

    Returns a dict: {score, reason, flagged}
    - score: 0-100, higher means higher risk
    - reason: short human-readable explanation
    - flagged: True if score >= threshold (triggers a payment hold)
    """
    baseline = PARTNERS.get(partner, DEFAULT_BASELINE)
    ratio = amount / baseline if baseline else 1.0

    raw_score = 18 + max(0, ratio - 1) * 70 + random.uniform(0, 6)
    score = int(min(97, max(4, round(raw_score))))
    flagged = score >= threshold

    if flagged:
        reason = f"Payment is {ratio:.1f}x {partner}'s typical order value."
    else:
        reason = f"Consistent with {partner}'s order history."

    return {"score": score, "reason": reason, "flagged": flagged, "threshold": threshold}


def partner_list():
    return list(PARTNERS.keys())
