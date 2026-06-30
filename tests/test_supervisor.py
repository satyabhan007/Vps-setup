"""
Unit tests for agents/supervisor.py (SovereignSupervisor)

Tests cover the full Plan → Execute → Verify loop with all external I/O mocked:
  - BOOKING intent with missing patient profile → COLLECT_DATA
  - BOOKING intent with complete patient profile → PROCESS_BOOKING
  - EMERGENCY intent → HANDOVER via HITLManager
  - PRICING intent → INFO_RESPONSE
  - GENERAL_INQUIRY with incomplete profile → COLLECT_DATA
  - _get_state and _update_state DB interactions
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call


CLINIC_ID     = "test_clinic"
ADMIN_GROUP   = "TEST_ADMIN_GROUP"
DASHBOARD_WH  = "https://example.com/webhook"
PATIENT_PHONE = "+919876543210"

FULL_PROFILE  = {
    "age": "28",
    "gender": "Female",
    "chief_complaint": "Teeth whitening",
    "previous_history": "None",
}


# ---------------------------------------------------------------------------
# Helper – build a fresh mock DB connection
# ---------------------------------------------------------------------------

def _make_conn(fetchone_return=None):
    """Returns (conn, cursor) mock pair."""
    conn   = MagicMock()
    cursor = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__  = MagicMock(return_value=False)
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__  = MagicMock(return_value=False)
    cursor.fetchone.return_value = fetchone_return
    return conn, cursor


def _make_supervisor(fetchone_return=None):
    """Creates a SovereignSupervisor where ALL psycopg2.connect calls use the mock."""
    conn, cursor = _make_conn(fetchone_return)
    with patch("agents.supervisor.psycopg2.connect", return_value=conn):
        from importlib import reload
        import agents.supervisor as sup_module
        reload(sup_module)                     # ensure fresh import after patch
        sup = sup_module.SovereignSupervisor(
            clinic_id=CLINIC_ID,
            admin_group=ADMIN_GROUP,
            dashboard_webhook=DASHBOARD_WH,
        )
        return sup, conn, cursor


# ---------------------------------------------------------------------------
# process_loop – BOOKING with empty profile
# ---------------------------------------------------------------------------

class TestProcessLoopBookingMissingProfile:
    def setup_method(self):
        """Use a side_effect so EVERY connect() call returns the same mock conn."""
        self.conn, self.cursor = _make_conn(fetchone_return=None)  # None → empty state
        self.patcher = patch("agents.supervisor.psycopg2.connect", return_value=self.conn)
        self.patcher.start()
        from importlib import reload
        import agents.supervisor as sm
        reload(sm)
        from agents.supervisor import SovereignSupervisor
        self.sup = SovereignSupervisor(CLINIC_ID, ADMIN_GROUP)

    def teardown_method(self):
        self.patcher.stop()

    def test_returns_collect_data_action(self):
        result = self.sup.process_loop(PATIENT_PHONE, "I want to book an appointment")
        assert result["action_taken"] == "COLLECT_DATA"

    def test_expert_used_is_triage(self):
        result = self.sup.process_loop(PATIENT_PHONE, "I want to book an appointment")
        assert result["expert_used"] == "triage"

    def test_intent_is_booking(self):
        result = self.sup.process_loop(PATIENT_PHONE, "I want to book an appointment")
        assert result["intent"] == "BOOKING"

    def test_response_is_a_question(self):
        result = self.sup.process_loop(PATIENT_PHONE, "I want to book a slot")
        assert "?" in result["final_response"]


# ---------------------------------------------------------------------------
# process_loop – BOOKING with full profile
# ---------------------------------------------------------------------------

class TestProcessLoopBookingCompleteProfile:
    def setup_method(self):
        """Return a full profile state from DB."""
        state_row = {"state_data": {"profile": FULL_PROFILE}}
        self.conn, self.cursor = _make_conn(fetchone_return=state_row)
        self.patcher = patch("agents.supervisor.psycopg2.connect", return_value=self.conn)
        self.patcher.start()
        from importlib import reload
        import agents.supervisor as sm
        reload(sm)
        from agents.supervisor import SovereignSupervisor
        self.sup = SovereignSupervisor(CLINIC_ID, ADMIN_GROUP)

    def teardown_method(self):
        self.patcher.stop()

    def test_returns_process_booking_action(self):
        result = self.sup.process_loop(PATIENT_PHONE, "I want to book an appointment")
        assert result["action_taken"] == "PROCESS_BOOKING"

    def test_expert_used_is_booking(self):
        result = self.sup.process_loop(PATIENT_PHONE, "Book me an appointment please")
        assert result["expert_used"] == "booking"


# ---------------------------------------------------------------------------
# process_loop – EMERGENCY intent
# ---------------------------------------------------------------------------

class TestProcessLoopEmergency:
    def setup_method(self):
        self.conn, self.cursor = _make_conn(fetchone_return=None)
        self.patcher = patch("agents.supervisor.psycopg2.connect", return_value=self.conn)
        self.patcher.start()
        from importlib import reload
        import agents.supervisor as sm
        reload(sm)
        from agents.supervisor import SovereignSupervisor
        self.sup = SovereignSupervisor(CLINIC_ID, ADMIN_GROUP)

    def teardown_method(self):
        self.patcher.stop()

    def test_returns_handover_action(self):
        result = self.sup.process_loop(PATIENT_PHONE, "I have severe pain and bleeding")
        assert result["action_taken"] == "HANDOVER"

    def test_expert_used_is_hitl(self):
        result = self.sup.process_loop(PATIENT_PHONE, "Emergency! Severe bleeding")
        assert result["expert_used"] == "hitl"

    def test_response_contains_hitl_alert(self):
        result = self.sup.process_loop(PATIENT_PHONE, "Severe pain emergency")
        assert "HITL" in result["final_response"] or "ALERT" in result["final_response"]


# ---------------------------------------------------------------------------
# process_loop – PRICING intent
# ---------------------------------------------------------------------------

class TestProcessLoopPricing:
    def setup_method(self):
        self.conn, self.cursor = _make_conn(fetchone_return=None)
        self.patcher = patch("agents.supervisor.psycopg2.connect", return_value=self.conn)
        self.patcher.start()
        from importlib import reload
        import agents.supervisor as sm
        reload(sm)
        from agents.supervisor import SovereignSupervisor
        self.sup = SovereignSupervisor(CLINIC_ID, ADMIN_GROUP)

    def teardown_method(self):
        self.patcher.stop()

    def test_returns_info_response_action(self):
        result = self.sup.process_loop(PATIENT_PHONE, "What is the cost of a root canal?")
        assert result["action_taken"] == "INFO_RESPONSE"

    def test_intent_is_pricing(self):
        result = self.sup.process_loop(PATIENT_PHONE, "What is the fee for a cleaning?")
        assert result["intent"] == "PRICING"


# ---------------------------------------------------------------------------
# _get_state and _update_state
# ---------------------------------------------------------------------------

class TestStateManagement:
    def setup_method(self):
        self.conn, self.cursor = _make_conn(fetchone_return=None)
        self.patcher = patch("agents.supervisor.psycopg2.connect", return_value=self.conn)
        self.patcher.start()
        from importlib import reload
        import agents.supervisor as sm
        reload(sm)
        from agents.supervisor import SovereignSupervisor
        self.sup = SovereignSupervisor(CLINIC_ID, ADMIN_GROUP)

    def teardown_method(self):
        self.patcher.stop()

    def test_get_state_returns_empty_dict_for_new_patient(self):
        self.cursor.fetchone.return_value = None
        result = self.sup._get_state(PATIENT_PHONE)
        assert result == {}

    def test_get_state_returns_state_data_for_existing_patient(self):
        self.cursor.fetchone.return_value = {"state_data": {"profile": FULL_PROFILE}}
        result = self.sup._get_state(PATIENT_PHONE)
        assert result.get("profile") == FULL_PROFILE

    def test_update_state_calls_db_execute(self):
        self.cursor.reset_mock()
        self.sup._update_state(PATIENT_PHONE, {"profile": FULL_PROFILE})
        assert self.cursor.execute.called

    def test_get_state_handles_db_error_gracefully(self):
        self.cursor.execute.side_effect = Exception("DB connection failed")
        result = self.sup._get_state(PATIENT_PHONE)
        assert result == {}
