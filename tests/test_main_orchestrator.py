"""
Unit tests for agents/main_orchestrator.py (LoopOrchestrator)

Tests the lightweight orchestrator that wires TriageProfiler, HITLManager,
and BookingExecutor together. BookingExecutor is mocked to avoid credential I/O.

Tests:
  - handle_message: EMERGENCY → HANDOVER
  - handle_message: BOOKING with missing data → PROFILING
  - handle_message: BOOKING with complete data → BOOKING_PROCESS
  - handle_message: PRICING → RESPONSE
  - handle_message: GENERAL_INQUIRY missing profile → PROFILING
  - handle_message: GENERAL_INQUIRY complete profile → general RESPONSE
"""

import pytest
from unittest.mock import MagicMock, patch


CLINIC_ID     = "test_clinic"
ADMIN_GROUP   = "TEST_ADMIN_GROUP"
DASHBOARD_WH  = "https://example.com/webhook"
PATIENT_PHONE = "+919876543210"

FULL_PROFILE = {
    "age": "30",
    "gender": "Male",
    "chief_complaint": "Routine cleaning",
    "previous_history": "None",
}


@pytest.fixture
def orchestrator():
    """LoopOrchestrator with BookingExecutor's credential loading mocked out."""
    with patch("agents.executor_booking.BookingExecutor._load_creds", return_value=MagicMock()), \
         patch("agents.executor_booking.build", return_value=MagicMock()):
        from agents.main_orchestrator import LoopOrchestrator
        return LoopOrchestrator(
            clinic_id=CLINIC_ID,
            admin_group=ADMIN_GROUP,
            dashboard_webhook=DASHBOARD_WH,
        )


# ---------------------------------------------------------------------------
# EMERGENCY
# ---------------------------------------------------------------------------

class TestHandleMessageEmergency:
    def test_emergency_returns_handover_action(self, orchestrator):
        result = orchestrator.handle_message(PATIENT_PHONE, "I am bleeding heavily!")
        assert result["action"] == "HANDOVER"

    def test_emergency_response_contains_alert(self, orchestrator):
        result = orchestrator.handle_message(PATIENT_PHONE, "Severe pain emergency")
        assert "HITL" in result["response"] or "ALERT" in result["response"]

    def test_emergency_has_hitl_status(self, orchestrator):
        result = orchestrator.handle_message(PATIENT_PHONE, "Severe bleeding pain")
        assert result["status"] == "HUMAN_REQUIRED_IMMEDIATE"


# ---------------------------------------------------------------------------
# BOOKING
# ---------------------------------------------------------------------------

class TestHandleMessageBooking:
    def test_booking_with_missing_data_returns_profiling(self, orchestrator):
        result = orchestrator.handle_message(
            PATIENT_PHONE, "I want to book a cleaning", patient_data={"age": "25"}
        )
        assert result["action"] == "PROFILING"

    def test_booking_missing_data_includes_missing_fields(self, orchestrator):
        result = orchestrator.handle_message(
            PATIENT_PHONE, "I want to book a slot", patient_data={}
        )
        assert "missing_fields" in result
        assert len(result["missing_fields"]) > 0

    def test_booking_with_complete_data_returns_booking_process(self, orchestrator):
        result = orchestrator.handle_message(
            PATIENT_PHONE, "I want to book a cleaning", patient_data=FULL_PROFILE
        )
        assert result["action"] == "BOOKING_PROCESS"

    def test_booking_process_mentions_executor_agent(self, orchestrator):
        result = orchestrator.handle_message(
            PATIENT_PHONE, "Book me an appointment", patient_data=FULL_PROFILE
        )
        assert result.get("agent") == "executor_booking"


# ---------------------------------------------------------------------------
# PRICING
# ---------------------------------------------------------------------------

class TestHandleMessagePricing:
    def test_pricing_returns_response_action(self, orchestrator):
        result = orchestrator.handle_message(PATIENT_PHONE, "What is the cost of a root canal?")
        assert result["action"] == "RESPONSE"

    def test_pricing_response_is_non_empty(self, orchestrator):
        result = orchestrator.handle_message(PATIENT_PHONE, "How much does a cleaning cost?")
        assert isinstance(result["response"], str) and len(result["response"]) > 0


# ---------------------------------------------------------------------------
# GENERAL INQUIRY
# ---------------------------------------------------------------------------

class TestHandleMessageGeneral:
    def test_general_with_missing_profile_returns_profiling(self, orchestrator):
        result = orchestrator.handle_message(
            PATIENT_PHONE, "What are your hours?", patient_data={}
        )
        assert result["action"] == "PROFILING"

    def test_general_with_complete_profile_returns_response(self, orchestrator):
        result = orchestrator.handle_message(
            PATIENT_PHONE, "What are your hours?", patient_data=FULL_PROFILE
        )
        assert result["action"] == "RESPONSE"

    def test_defaults_patient_data_to_empty_dict(self, orchestrator):
        """Calling without patient_data should not raise."""
        result = orchestrator.handle_message(PATIENT_PHONE, "Hello")
        assert "action" in result

    def test_defaults_chat_history_to_empty_list(self, orchestrator):
        """Calling without chat_history should not raise."""
        result = orchestrator.handle_message(PATIENT_PHONE, "Hi")
        assert "action" in result
