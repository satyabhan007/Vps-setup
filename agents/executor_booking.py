import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class BookingExecutor:
    def __init__(self, clinic_id):
        self.clinic_id = clinic_id
        # Lazy-loaded to allow testing without real credentials
        self._creds = None
        self._service = None

    def _load_creds(self, clinic_id):
        """Loads clinic-specific Google Calendar credentials.
        In production, fetches from encrypted Postgres store.
        """
        return Credentials.from_authorized_user_file(f"creds_{clinic_id}.json")

    @property
    def creds(self):
        if self._creds is None:
            self._creds = self._load_creds(self.clinic_id)
        return self._creds

    @property
    def service(self):
        if self._service is None:
            self._service = build("calendar", "v3", credentials=self.creds)
        return self._service

    def check_availability(self, start_time, end_time):
        """Deterministic check for calendar conflicts.
        Returns True if the slot is free, False if busy.
        """
        events_result = self.service.events().list(
            calendarId="primary",
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
        ).execute()
        events = events_result.get("items", [])
        return len(events) == 0

    def book_slot(self, patient_name, start_time, end_time):
        """Deterministically books a calendar slot.
        Returns the created event dict from Google Calendar API.
        """
        event = {
            "summary": f"Patient: {patient_name}",
            "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"},
        }
        return self.service.events().insert(calendarId="primary", body=event).execute()


# This agent is called by n8n via a Python function node
