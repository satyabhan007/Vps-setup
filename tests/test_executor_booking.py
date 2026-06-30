"""
Unit tests for agents/executor_booking.py

Tests:
  - check_availability: free slot (no events), busy slot (events exist)
  - book_slot: correct event payload, correct timezone (Asia/Kolkata)
  - Lazy credential loading does not call file I/O during construction
"""

import pytest
from unittest.mock import MagicMock, patch
from agents.executor_booking import BookingExecutor


CLINIC_ID = "test_clinic"


@pytest.fixture
def executor():
    """BookingExecutor with a fully mocked Google Calendar service."""
    ex = BookingExecutor(clinic_id=CLINIC_ID)
    mock_service = MagicMock()
    ex._service = mock_service
    ex._creds = MagicMock()
    return ex


# ---------------------------------------------------------------------------
# Lazy loading
# ---------------------------------------------------------------------------

class TestLazyLoading:
    def test_construction_does_not_call_credentials_file(self):
        """Constructing BookingExecutor must NOT touch the filesystem."""
        with patch.object(BookingExecutor, "_load_creds") as mock_load:
            BookingExecutor(clinic_id=CLINIC_ID)
            mock_load.assert_not_called()

    def test_service_is_none_before_first_access(self):
        ex = BookingExecutor(clinic_id=CLINIC_ID)
        assert ex._service is None
        assert ex._creds is None


# ---------------------------------------------------------------------------
# check_availability
# ---------------------------------------------------------------------------

class TestCheckAvailability:
    START = "2026-07-01T09:00:00+05:30"
    END = "2026-07-01T09:30:00+05:30"

    def test_returns_true_when_no_events(self, executor):
        executor.service.events().list().execute.return_value = {"items": []}
        assert executor.check_availability(self.START, self.END) is True

    def test_returns_false_when_events_exist(self, executor):
        executor.service.events().list().execute.return_value = {
            "items": [{"id": "event1", "summary": "Existing Appointment"}]
        }
        assert executor.check_availability(self.START, self.END) is False

    def test_returns_false_when_multiple_events_exist(self, executor):
        executor.service.events().list().execute.return_value = {
            "items": [{"id": f"evt{i}"} for i in range(3)]
        }
        assert executor.check_availability(self.START, self.END) is False

    def test_passes_correct_time_range_to_api(self, executor):
        executor.service.events().list().execute.return_value = {"items": []}
        executor.check_availability(self.START, self.END)
        call_kwargs = executor.service.events().list.call_args[1]
        assert call_kwargs["timeMin"] == self.START
        assert call_kwargs["timeMax"] == self.END

    def test_uses_primary_calendar(self, executor):
        executor.service.events().list().execute.return_value = {"items": []}
        executor.check_availability(self.START, self.END)
        call_kwargs = executor.service.events().list.call_args[1]
        assert call_kwargs["calendarId"] == "primary"


# ---------------------------------------------------------------------------
# book_slot
# ---------------------------------------------------------------------------

class TestBookSlot:
    START = "2026-07-01T10:00:00+05:30"
    END = "2026-07-01T10:30:00+05:30"
    PATIENT = "Ravi Kumar"

    def _setup_mock_insert(self, executor, return_val=None):
        mock_event = return_val or {"id": "new_event_123", "summary": f"Patient: {self.PATIENT}"}
        executor.service.events().insert().execute.return_value = mock_event
        return mock_event

    def test_returns_created_event_dict(self, executor):
        expected = self._setup_mock_insert(executor)
        result = executor.book_slot(self.PATIENT, self.START, self.END)
        assert result == expected

    def test_event_summary_contains_patient_name(self, executor):
        self._setup_mock_insert(executor)
        executor.book_slot(self.PATIENT, self.START, self.END)
        body = executor.service.events().insert.call_args[1]["body"]
        assert self.PATIENT in body["summary"]

    def test_event_uses_asia_kolkata_timezone(self, executor):
        self._setup_mock_insert(executor)
        executor.book_slot(self.PATIENT, self.START, self.END)
        body = executor.service.events().insert.call_args[1]["body"]
        assert body["start"]["timeZone"] == "Asia/Kolkata"
        assert body["end"]["timeZone"] == "Asia/Kolkata"

    def test_event_uses_correct_start_and_end_times(self, executor):
        self._setup_mock_insert(executor)
        executor.book_slot(self.PATIENT, self.START, self.END)
        body = executor.service.events().insert.call_args[1]["body"]
        assert body["start"]["dateTime"] == self.START
        assert body["end"]["dateTime"] == self.END

    def test_inserts_into_primary_calendar(self, executor):
        self._setup_mock_insert(executor)
        executor.book_slot(self.PATIENT, self.START, self.END)
        call_kwargs = executor.service.events().insert.call_args[1]
        assert call_kwargs["calendarId"] == "primary"
