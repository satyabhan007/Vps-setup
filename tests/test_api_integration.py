"""
Integration tests for the FastAPI application (main.py).

Uses FastAPI's TestClient (HTTPX-based) to test the full request/response cycle.
The SovereignSupervisor is replaced with a mock to avoid any DB/network I/O.

Tests:
  - GET /health → 200 + correct payload
  - POST /process with booking message + empty profile → COLLECT_DATA response
  - POST /process with complete profile → PROCESS_BOOKING response
  - POST /process with emergency message → HANDOVER response
  - POST /process with pricing message → INFO_RESPONSE
  - POST /process malformed body → 422
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mock_supervisor():
    """A fully mocked SovereignSupervisor for the API tests."""
    sup = MagicMock()
    sup._get_state.return_value = {}
    return sup


@pytest.fixture(scope="module")
def client(mock_supervisor):
    """TestClient with the supervisor pre-injected. Avoids DB startup."""
    with patch("agents.supervisor.psycopg2.connect"):
        import main
        main.supervisor = mock_supervisor
        yield TestClient(main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_payload_has_status_healthy(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_payload_has_agent_name(self, client):
        response = client.get("/health")
        data = response.json()
        assert "agent" in data
        assert "Supervisor" in data["agent"]


# ---------------------------------------------------------------------------
# POST /process – booking, incomplete profile
# ---------------------------------------------------------------------------

class TestProcessBookingIncompleteProfile:
    def test_returns_200(self, client, mock_supervisor):
        mock_supervisor.process_loop.return_value = {
            "final_response": "Could you please tell me your age?",
            "expert_used": "triage",
            "action_taken": "COLLECT_DATA",
            "intent": "BOOKING",
        }
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "I want to book an appointment",
        })
        assert response.status_code == 200

    def test_response_status_is_success(self, client, mock_supervisor):
        mock_supervisor.process_loop.return_value = {
            "final_response": "Could you please tell me your age?",
            "expert_used": "triage",
            "action_taken": "COLLECT_DATA",
            "intent": "BOOKING",
        }
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "Book an appointment please",
        })
        assert response.json()["status"] == "success"

    def test_data_contains_action_taken(self, client, mock_supervisor):
        mock_supervisor.process_loop.return_value = {
            "final_response": "Could you please tell me your age?",
            "expert_used": "triage",
            "action_taken": "COLLECT_DATA",
            "intent": "BOOKING",
        }
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "I want a slot for tomorrow",
        })
        assert response.json()["data"]["action_taken"] == "COLLECT_DATA"


# ---------------------------------------------------------------------------
# POST /process – booking, complete profile
# ---------------------------------------------------------------------------

class TestProcessBookingCompleteProfile:
    def test_returns_process_booking(self, client, mock_supervisor):
        mock_supervisor.process_loop.return_value = {
            "final_response": "I have all your details. Checking the calendar now...",
            "expert_used": "booking",
            "action_taken": "PROCESS_BOOKING",
            "intent": "BOOKING",
        }
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "I want to book an appointment",
            "patient_data": {
                "age": "30", "gender": "Male",
                "chief_complaint": "Root canal", "previous_history": "None"
            },
        })
        assert response.json()["data"]["action_taken"] == "PROCESS_BOOKING"
        assert response.json()["data"]["expert_used"] == "booking"


# ---------------------------------------------------------------------------
# POST /process – emergency
# ---------------------------------------------------------------------------

class TestProcessEmergency:
    def test_returns_handover(self, client, mock_supervisor):
        mock_supervisor.process_loop.return_value = {
            "final_response": "⚠️ HITL ALERT ⚠️\nPlease take over this chat.",
            "expert_used": "hitl",
            "action_taken": "HANDOVER",
            "intent": "EMERGENCY/CRITICAL",
        }
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "I have severe pain and bleeding",
        })
        assert response.json()["data"]["action_taken"] == "HANDOVER"
        assert response.json()["data"]["expert_used"] == "hitl"


# ---------------------------------------------------------------------------
# POST /process – pricing
# ---------------------------------------------------------------------------

class TestProcessPricing:
    def test_returns_info_response(self, client, mock_supervisor):
        mock_supervisor.process_loop.return_value = {
            "final_response": "I can provide our general price list...",
            "expert_used": "triage",
            "action_taken": "INFO_RESPONSE",
            "intent": "PRICING",
        }
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "What is the cost of a root canal?",
        })
        assert response.json()["data"]["action_taken"] == "INFO_RESPONSE"
        assert response.json()["data"]["intent"] == "PRICING"


# ---------------------------------------------------------------------------
# POST /process – validation
# ---------------------------------------------------------------------------

class TestProcessValidation:
    def test_missing_patient_phone_returns_422(self, client):
        response = client.post("/process", json={"message": "Hello"})
        assert response.status_code == 422

    def test_missing_message_returns_422(self, client):
        response = client.post("/process", json={"patient_phone": "+919876543210"})
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        response = client.post("/process", json={})
        assert response.status_code == 422

    def test_extra_fields_are_ignored(self, client, mock_supervisor):
        """Pydantic should ignore extra unknown fields without error."""
        mock_supervisor.process_loop.return_value = {
            "final_response": "Hello!",
            "expert_used": "triage",
            "action_taken": "GENERAL_HELP",
            "intent": "GENERAL_INQUIRY",
        }
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "Hi",
            "unknown_field": "some_value",
        })
        assert response.status_code == 200

    def test_supervisor_exception_returns_500(self, client, mock_supervisor):
        """If the supervisor raises an exception, the endpoint should return 500."""
        mock_supervisor.process_loop.side_effect = RuntimeError("DB connection lost")
        response = client.post("/process", json={
            "patient_phone": "+919876543210",
            "message": "Hello",
        })
        assert response.status_code == 500
        # Reset side effect for subsequent tests
        mock_supervisor.process_loop.side_effect = None
