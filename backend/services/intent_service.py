"""
intent_service.py — Query Intent Recognition

Classifies incoming user queries into one of several support intents using
keyword heuristics combined with an optional LLM fallback.  The detected
intent is surfaced in the /intent API endpoint and is also injected into
RAG prompts so the LLM can tailor its tone (e.g. empathetic for billing
disputes, technical for API errors).

Supported intents:
  billing         — pricing, invoices, payment, subscriptions
  troubleshooting — errors, crashes, not working, reset
  account         — login, password, 2FA, locked account
  integrations    — Slack, Teams, Zapier, webhooks
  api             — API keys, endpoints, rate limits, developer
  feature_request — suggestion, would like, feature, improve
  general         — anything else / uncertain
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Intent taxonomy
# ---------------------------------------------------------------------------

INTENTS: dict[str, list[str]] = {
    "billing": [
        r"\bbill\b", r"\binvoice\b", r"\bpayment\b", r"\bprice\b", r"\bpricing\b",
        r"\bplan\b", r"\bsubscri", r"\brefund\b", r"\bcharge\b", r"\bcard\b",
        r"\bupgrade\b", r"\bdowngrade\b", r"\btrial\b", r"\bcost\b",
    ],
    "troubleshooting": [
        r"\berror\b", r"\bnot work", r"\bcrash", r"\bfail", r"\bbug\b",
        r"\bissue\b", r"\bproblem\b", r"\bbroken\b", r"\bslow\b", r"\bfreez",
        r"\bwon'?t\b", r"\bcan'?t\b", r"\bunable\b", r"\bfix\b", r"\btrouble",
        r"\bloading\b", r"\btimeout\b", r"\bdown\b",
    ],
    "account": [
        r"\bpassword\b", r"\blogin\b", r"\blog in\b", r"\bsign in\b",
        r"\baccount\b", r"\blocked\b", r"\b2fa\b", r"\btwo.?factor\b",
        r"\bverif", r"\bemail\b", r"\breset\b", r"\bregister\b", r"\bsign up\b",
        r"\bpermission\b", r"\brole\b", r"\binvite\b",
    ],
    "integrations": [
        r"\bintegrat", r"\bslack\b", r"\bteams\b", r"\bzapier\b",
        r"\bwebhook\b", r"\bsalesforce\b", r"\bhubspot\b", r"\bconnect\b",
        r"\bsync\b", r"\bautomation\b", r"\btrigger\b",
    ],
    "api": [
        r"\bapi\b", r"\bapi key\b", r"\bendpoint\b", r"\brate limit\b",
        r"\bdeveloper\b", r"\bsdks?\b", r"\brest\b", r"\bjson\b",
        r"\bauthentication\b", r"\btoken\b", r"\boauth\b", r"\bcurl\b",
        r"\bprogrammatic\b",
    ],
    "feature_request": [
        r"\bfeature\b", r"\bsuggest", r"\bwish\b", r"\bwould (like|love|want)\b",
        r"\benhance", r"\bimprove\b", r"\badd (support|the ability)\b",
        r"\bplease (add|include|support)\b",
    ],
}

INTENT_LABELS: dict[str, str] = {
    "billing": "Billing & Subscription",
    "troubleshooting": "Troubleshooting",
    "account": "Account & Login",
    "integrations": "Integrations",
    "api": "API & Developer",
    "feature_request": "Feature Request",
    "general": "General Inquiry",
}

INTENT_EMOJI: dict[str, str] = {
    "billing": "💳",
    "troubleshooting": "🔧",
    "account": "🔐",
    "integrations": "🔗",
    "api": "⚙️",
    "feature_request": "💡",
    "general": "💬",
}


# ---------------------------------------------------------------------------
# Core classifier
# ---------------------------------------------------------------------------

@dataclass
class IntentResult:
    intent: str
    label: str
    emoji: str
    confidence: float          # 0.0 – 1.0  (heuristic score)
    matched_patterns: list[str]


def classify_intent(text: str) -> IntentResult:
    """
    Classify *text* into one of the predefined intents.

    Returns an IntentResult with the best-matching intent and a
    heuristic confidence score.  When multiple intents tie, the one
    listed first in INTENTS wins.
    """
    lowered = text.lower()
    scores: dict[str, int] = {}

    for intent, patterns in INTENTS.items():
        hits = [p for p in patterns if re.search(p, lowered)]
        if hits:
            scores[intent] = len(hits)

    if not scores:
        return IntentResult(
            intent="general",
            label=INTENT_LABELS["general"],
            emoji=INTENT_EMOJI["general"],
            confidence=0.5,
            matched_patterns=[],
        )

    best_intent = max(scores, key=lambda k: scores[k])
    total_patterns = len(INTENTS[best_intent])
    confidence = min(scores[best_intent] / max(total_patterns, 1), 1.0)
    # Boost confidence when the score is clearly dominant
    if len(scores) > 1:
        sorted_scores = sorted(scores.values(), reverse=True)
        if sorted_scores[0] > sorted_scores[1]:
            confidence = min(confidence + 0.2, 1.0)

    matched = [p for p in INTENTS[best_intent] if re.search(p, lowered)]

    return IntentResult(
        intent=best_intent,
        label=INTENT_LABELS[best_intent],
        emoji=INTENT_EMOJI[best_intent],
        confidence=round(confidence, 2),
        matched_patterns=matched,
    )


def get_intent_context(intent: str) -> str:
    """Return a short instruction string injected into RAG prompts."""
    snippets: dict[str, str] = {
        "billing": "The user has a billing or subscription question. Be clear about pricing details.",
        "troubleshooting": "The user is reporting a technical problem. Provide step-by-step resolution guidance.",
        "account": "The user has an account or authentication question. Be reassuring and precise.",
        "integrations": "The user needs help with a third-party integration. Mention configuration steps.",
        "api": "The user is a developer asking about the API. Include relevant technical details.",
        "feature_request": "The user is suggesting a feature. Acknowledge their feedback warmly.",
        "general": "",
    }
    return snippets.get(intent, "")
