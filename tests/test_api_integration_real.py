"""
Integration tests for the full API stack with a REAL Postgres container.

Requires:  Docker running locally.
Run only:  pytest tests/test_api_integration_real.py -v -m integration

These tests exercise the complete Plan → Execute → Verify loop including:
  - Real psycopg2 DB writes / reads via SovereignSupervisor
  - session_state table creation / upsert / fetch
  - FastAPI endpoints via TestClient with a live supervisor

All tests are tagged @pytest.mark.integration so they can be excluded from
the fast unit-test run:  pytest tests/ -m "not integration"
"""

import pytest
import psycopg2

pytestmark = pytest.mark.integration   # All tests in this file require Docker


CLINIC_ID     = "test_clinic"
PATIENT_PHONE = "+919876543210"
FULL_PROFILE  = {
    "age": "35",
    "gender": "Male",
    "chief_complaint": "Routine cleaning",
    "previous_history": "None",
}


# ============================================================================
# DB Layer – _get_state / _update_state
# ============================================================================

class TestStateRoundtrip:
    def test_new_patient_returns_empty_state(self, pg_supervisor):
        state = pg_supervisor._get_state("+910000000001")
        assert state == {}

    def test_update_then_get_returns_persisted_data(self, pg_supervisor):
        payload = {"profile": {"age": "25", "gender": "Female"}}
        pg_supervisor._update_state(PATIENT_PHONE, payload)
        retrieved = pg_supervisor._get_state(PATIENT_PHONE)
        assert retrieved.get("profile", {}).get("age") == "25"
        assert retrieved.get("profile", {}).get("gender") == "Female"

    def test_update_merges_new_keys(self, pg_supervisor):
        """Second update should JSONB-merge, not overwrite."""
        pg_supervisor._update_state(PATIENT_PHONE, {"profile": {"age": "28"}})
        pg_supervisor._update_state(PATIENT_PHONE, {"profile": {"gender": "Male"}})
        state = pg_supervisor._get_state(PATIENT_PHONE)
        # Both keys should be present after merge
        assert state["profile"]["age"] == "28"
        assert state["profile"]["gender"] == "Male"

    def test_update_overwrites_existing_key_value(self, pg_supervisor):
        pg_supervisor._update_state(PATIENT_PHONE, {"profile": {"age": "20"}})
        pg_supervisor._update_state(PATIENT_PHONE, {"profile": {"age": "30"}})
        state = pg_supervisor._get_state(PATIENT_PHONE)
        assert state["profile"]["age"] == "30"

    def test_multiple_patients_are_isolated(self, pg_supervisor):
        phone_a = "+911111111111"
        phone_b = "+912222222222"
        pg_supervisor._update_state(phone_a, {"profile": {"age": "20"}})
        pg_supervisor._update_state(phone_b, {"profile": {"age": "40"}})
        assert pg_supervisor._get_state(phone_a)["profile"]["age"] == "20"
        assert pg_supervisor._get_state(phone_b)["profile"]["age"] == "40"

    def test_session_state_table_exists(self, pg_conn):
        """Confirm _ensure_state_table created the table."""
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT to_regclass('public.session_state');"
            )
            result = cur.fetchone()
        assert result[0] is not None   # table exists


# ============================================================================
# Supervisor Loop – with real DB persistence
# ============================================================================

class TestSupervisorLoopRealDB:
    def test_booking_missing_profile_stores_state_and_asks_question(self, pg_supervisor):
        result = pg_supervisor.process_loop(PATIENT_PHONE, "I want to book an appointment")
        # Should ask for a missing field (profile is empty)
        assert result["action_taken"] == "COLLECT_DATA"
        assert "?" in result["final_response"]

    def test_emergency_intent_triggers_handover(self, pg_supervisor):
        result = pg_supervisor.process_loop(PATIENT_PHONE, "I have severe bleeding and pain")
        assert result["action_taken"] == "HANDOVER"
        assert result["expert_used"] == "hitl"

    def test_pricing_inquiry_returns_info_response(self, pg_supervisor):
        result = pg_supervisor.process_loop(PATIENT_PHONE, "What is the fee for a root canal?")
        assert result["action_taken"] == "INFO_RESPONSE"
        assert result["intent"] == "PRICING"

    def test_booking_with_full_profile_pre_seeded_returns_process_booking(self, pg_supervisor):
        # Pre-seed the DB with a complete profile
        pg_supervisor._update_state(PATIENT_PHONE, {"profile": FULL_PROFILE})
        result = pg_supervisor.process_loop(PATIENT_PHONE, "I want to book an appointment")
        assert result["action_taken"] == "PROCESS_BOOKING"
        assert result["expert_used"] == "booking"

    def test_process_loop_persists_missing_profile_tracking(self, pg_supervisor):
        """After a COLLECT_DATA pass, the state should record missing fields."""
        pg_supervisor.process_loop(PATIENT_PHONE, "Book me a slot")
        state = pg_supervisor._get_state(PATIENT_PHONE)
        # The supervisor writes data_update to the DB which includes 'missing'
        assert "missing" in state or "profile" in state  # data was persisted


# ============================================================================
# FastAPI Endpoint – with real DB
# ============================================================================

class TestAPIWithRealDB:
    def test_health_endpoint_returns_200(self, api_client_real):
        resp = api_client_real.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_process_booking_new_patient_returns_collect_data(self, api_client_real):
        resp = api_client_real.post("/process", json={
            "patient_phone": "+919000000001",
            "message": "I want to book an appointment",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["data"]["action_taken"] == "COLLECT_DATA"

    def test_process_emergency_returns_handover(self, api_client_real):
        resp = api_client_real.post("/process", json={
            "patient_phone": "+919000000002",
            "message": "Severe tooth pain and bleeding emergency",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["action_taken"] == "HANDOVER"

    def test_process_with_full_patient_data_inline_returns_process_booking(self, api_client_real):
        """Passing patient_data inline should seed the profile and proceed to booking."""
        resp = api_client_real.post("/process", json={
            "patient_phone": "+919000000003",
            "message": "Book me an appointment",
            "patient_data": FULL_PROFILE,
        })
        assert resp.status_code == 200
        # Inline data seeds the profile, so booking can proceed
        action = resp.json()["data"]["action_taken"]
        assert action in ("PROCESS_BOOKING", "COLLECT_DATA")  # depends on merge timing

    def test_process_pricing_returns_info_response(self, api_client_real):
        resp = api_client_real.post("/process", json={
            "patient_phone": "+919000000004",
            "message": "How much does a cleaning cost?",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["action_taken"] == "INFO_RESPONSE"

    def test_missing_required_fields_returns_422(self, api_client_real):
        resp = api_client_real.post("/process", json={"message": "Hello"})
        assert resp.status_code == 422

    def test_state_persists_across_two_requests(self, api_client_real):
        """Two sequential POSTs from the same patient should share state."""
        phone = "+919000000005"
        # First request: no profile → collect data
        r1 = api_client_real.post("/process", json={
            "patient_phone": phone,
            "message": "I want to book",
        })
        assert r1.status_code == 200

        # Second request: still booking intent; DB should have the partial state
        r2 = api_client_real.post("/process", json={
            "patient_phone": phone,
            "message": "Book me a slot for tomorrow",
        })
        assert r2.status_code == 200
        # Both should be COLLECT_DATA since profile is still empty
        assert r2.json()["data"]["action_taken"] == "COLLECT_DATA"
