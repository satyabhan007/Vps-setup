"""
Unit tests for agents/hitl_manager.py

Tests:
  - evaluate_confidence: all 3 return values (EMERGENCY, low confidence, AI confirmed)
  - trigger_handover: alert message format, webhook POST call
"""

import pytest
from unittest.mock import patch, MagicMock
from agents.hitl_manager import HITLManager


ADMIN_GROUP = "TEST_ADMIN_GROUP"
DASHBOARD_WEBHOOK = "https://example.com/webhook"
PATIENT_PHONE = "+919876543210"


@pytest.fixture
def hitl():
    return HITLManager(admin_whatsapp_group=ADMIN_GROUP, dashboard_webhook=DASHBOARD_WEBHOOK)


@pytest.fixture
def hitl_no_webhook():
    return HITLManager(admin_whatsapp_group=ADMIN_GROUP, dashboard_webhook=None)


# ---------------------------------------------------------------------------
# evaluate_confidence
# ---------------------------------------------------------------------------

class TestEvaluateConfidence:
    def test_emergency_intent_requires_immediate_human(self, hitl):
        result = hitl.evaluate_confidence("", 1.0, "EMERGENCY")
        assert result == "HUMAN_REQUIRED_IMMEDIATE"

    def test_low_confidence_score_requires_review(self, hitl):
        result = hitl.evaluate_confidence("Here is my response", 0.5, "BOOKING")
        assert result == "HUMAN_REQUIRED_REVIEW"

    def test_boundary_confidence_below_threshold(self, hitl):
        """Score of exactly 0.69 should still trigger review."""
        result = hitl.evaluate_confidence("Response", 0.69, "GENERAL_INQUIRY")
        assert result == "HUMAN_REQUIRED_REVIEW"

    def test_boundary_confidence_at_threshold_passes(self, hitl):
        """Score of exactly 0.7 should be AI_CONFIRMED."""
        result = hitl.evaluate_confidence("Response", 0.7, "GENERAL_INQUIRY")
        assert result == "AI_CONFIRMED"

    def test_unsure_phrase_in_response_triggers_review(self, hitl):
        result = hitl.evaluate_confidence("I'm not sure about this.", 0.9, "PRICING")
        assert result == "HUMAN_REQUIRED_REVIEW"

    def test_apologetic_phrase_in_response_triggers_review(self, hitl):
        result = hitl.evaluate_confidence("I apologize for the confusion.", 0.95, "BOOKING")
        assert result == "HUMAN_REQUIRED_REVIEW"

    def test_high_confidence_normal_intent_confirms_ai(self, hitl):
        result = hitl.evaluate_confidence("Your appointment is confirmed.", 0.95, "BOOKING")
        assert result == "AI_CONFIRMED"

    def test_general_inquiry_high_confidence_confirmed(self, hitl):
        result = hitl.evaluate_confidence("We are open 9am to 6pm.", 0.85, "GENERAL_INQUIRY")
        assert result == "AI_CONFIRMED"


# ---------------------------------------------------------------------------
# trigger_handover
# ---------------------------------------------------------------------------

class TestTriggerHandover:
    def test_alert_message_contains_patient_phone(self, hitl):
        msg = hitl.trigger_handover(PATIENT_PHONE, [], reason="Low Confidence")
        assert PATIENT_PHONE in msg

    def test_alert_message_contains_reason(self, hitl):
        msg = hitl.trigger_handover(PATIENT_PHONE, [], reason="EMERGENCY_DETECTED")
        assert "EMERGENCY_DETECTED" in msg

    def test_alert_message_contains_hitl_marker(self, hitl):
        msg = hitl.trigger_handover(PATIENT_PHONE, [])
        assert "HITL" in msg

    def test_alert_includes_last_chat_message(self, hitl):
        history = ["Hello", "I have severe pain"]
        msg = hitl.trigger_handover(PATIENT_PHONE, history)
        assert "I have severe pain" in msg

    def test_alert_handles_empty_history(self, hitl):
        """Should not raise even with an empty chat history."""
        msg = hitl.trigger_handover(PATIENT_PHONE, [])
        assert "No history" in msg

    def test_webhook_post_is_called_when_configured(self, hitl):
        with patch("agents.hitl_manager.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            hitl.trigger_handover(PATIENT_PHONE, ["Hello"], reason="Test")
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == DASHBOARD_WEBHOOK  # URL
            payload = call_args[1]["json"]
            assert payload["patient_phone"] == PATIENT_PHONE
            assert payload["status"] == "PENDING_HUMAN"

    def test_no_webhook_call_when_not_configured(self, hitl_no_webhook):
        with patch("agents.hitl_manager.requests.post") as mock_post:
            hitl_no_webhook.trigger_handover(PATIENT_PHONE, [])
            mock_post.assert_not_called()

    def test_webhook_failure_does_not_raise(self, hitl):
        """A failed webhook POST should be swallowed gracefully."""
        with patch("agents.hitl_manager.requests.post", side_effect=Exception("Connection refused")):
            # Should not raise
            result = hitl.trigger_handover(PATIENT_PHONE, [])
            assert result is not None
