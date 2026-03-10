"""
Unit tests for services/intent_service.py.

The intent classifier uses pure keyword heuristics — no LLM calls are made —
so these tests run without any external dependencies or API keys.
"""
import pytest
from services.intent_service import classify_intent, get_intent_context, IntentResult, INTENT_LABELS, INTENT_EMOJI


# ===========================================================================
# classify_intent — keyword matching
# ===========================================================================

class TestClassifyIntentKeywords:
    """Each intent should be triggered by its representative keywords."""

    def test_billing_invoice(self):
        result = classify_intent("I have a question about my invoice")
        assert result.intent == "billing"

    def test_billing_payment(self):
        result = classify_intent("My payment failed on the credit card")
        assert result.intent == "billing"

    def test_billing_subscription(self):
        result = classify_intent("I need to upgrade my subscription plan")
        assert result.intent == "billing"

    def test_troubleshooting_error(self):
        result = classify_intent("I keep getting an error when I log in")
        assert result.intent in ("troubleshooting", "account")

    def test_troubleshooting_not_working(self):
        result = classify_intent("The dashboard is not working at all")
        assert result.intent == "troubleshooting"

    def test_troubleshooting_crash(self):
        result = classify_intent("The app crashes every time I open it")
        assert result.intent == "troubleshooting"

    def test_account_password(self):
        result = classify_intent("I forgot my password and can't log in")
        assert result.intent in ("account", "troubleshooting")

    def test_account_2fa(self):
        result = classify_intent("I can't set up 2FA on my account")
        assert result.intent == "account"

    def test_account_login(self):
        result = classify_intent("How do I sign in to my account?")
        assert result.intent == "account"

    def test_integrations_slack(self):
        result = classify_intent("How do I connect Slack to the platform?")
        assert result.intent == "integrations"

    def test_integrations_webhook(self):
        result = classify_intent("I need to set up a webhook for Zapier")
        assert result.intent == "integrations"

    def test_api_key(self):
        result = classify_intent("Where do I find my API key?")
        assert result.intent == "api"

    def test_api_endpoint(self):
        result = classify_intent("What are the REST endpoints for the developer SDK?")
        assert result.intent == "api"

    def test_feature_request_would_like(self):
        result = classify_intent("I would like to have dark mode in the app")
        assert result.intent == "feature_request"

    def test_feature_request_suggestion(self):
        result = classify_intent("Suggestion: please add CSV export feature")
        assert result.intent == "feature_request"


# ===========================================================================
# classify_intent — general / fallback
# ===========================================================================

class TestClassifyIntentGeneral:
    def test_vague_query_falls_back_to_general(self):
        result = classify_intent("Hi there, just checking in")
        assert result.intent == "general"

    def test_empty_string_returns_general(self):
        result = classify_intent("")
        assert result.intent == "general"

    def test_general_has_correct_label_and_emoji(self):
        result = classify_intent("hello world")
        assert result.label == INTENT_LABELS["general"]
        assert result.emoji == INTENT_EMOJI["general"]


# ===========================================================================
# classify_intent — IntentResult structure
# ===========================================================================

class TestIntentResultStructure:
    def test_result_is_intent_result_instance(self):
        result = classify_intent("I need help with my invoice")
        assert isinstance(result, IntentResult)

    def test_confidence_between_0_and_1(self):
        for text in [
            "My payment failed",
            "There is a bug in the API",
            "random text with no intent keywords",
        ]:
            result = classify_intent(text)
            assert 0.0 <= result.confidence <= 1.0, f"Out of range for: {text!r}"

    def test_matched_patterns_is_list(self):
        result = classify_intent("I have a billing question about my invoice")
        assert isinstance(result.matched_patterns, list)

    def test_matched_patterns_nonempty_for_known_intent(self):
        result = classify_intent("I have a billing question about my invoice")
        if result.intent != "general":
            assert len(result.matched_patterns) > 0

    def test_label_matches_intent(self):
        result = classify_intent("how do I use the API endpoint?")
        assert result.label == INTENT_LABELS[result.intent]

    def test_emoji_matches_intent(self):
        result = classify_intent("My payment failed")
        assert result.emoji == INTENT_EMOJI[result.intent]


# ===========================================================================
# classify_intent — case insensitivity
# ===========================================================================

class TestCaseInsensitivity:
    def test_uppercase_billing(self):
        result = classify_intent("INVOICE PAYMENT DUE")
        assert result.intent == "billing"

    def test_mixed_case_api(self):
        result = classify_intent("What are the API Endpoints?")
        assert result.intent == "api"


# ===========================================================================
# get_intent_context
# ===========================================================================

class TestGetIntentContext:
    @pytest.mark.parametrize("intent", [
        "billing", "troubleshooting", "account", "integrations", "api", "feature_request", "general",
    ])
    def test_returns_string_for_all_intents(self, intent):
        ctx = get_intent_context(intent)
        assert isinstance(ctx, str)

    def test_unknown_intent_returns_empty_or_string(self):
        ctx = get_intent_context("nonexistent_intent")
        assert isinstance(ctx, str)

    def test_billing_context_mentions_billing(self):
        ctx = get_intent_context("billing")
        assert "billing" in ctx.lower() or "pricing" in ctx.lower() or "subscription" in ctx.lower()
