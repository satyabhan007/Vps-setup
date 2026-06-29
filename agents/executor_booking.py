import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class BookingExecutor:
    def __init__(self, clinic_id):
        self.clinic_id = clinic_id
        # Load clinic-specific credentials from Postgres
        self.creds = self._load_creds(clinic_id)
        self.service = build('calendar', 'v3', credentials=self.creds)

    def _load_creds(self, clinic_id):
        # In production, fetch from encrypted Postgres store
        return Credentials.from_authorized_user_file(f'creds_{clinic_id}.json')

    def check_availability(self, start_time, end_time):
        """Deterministic check for calendar conflicts."""
        events_result = self.service.events().list(
            calendarId='primary', 
            timeMin=start_time, 
            timeMax=end_time, 
            singleEvents=True
        ).execute()
        events = events_result.get('items', [])
        return len(events) == 0

    def book_slot(self, patient_name, start_time, end_time):
        """Deterministic booking."""
        event = {
            'summary': f'Patient: {patient_name}',
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
        }
        return self.service.events().insert(calendarId='primary', body=event).execute()

# This agent is called by n8n via a Python function node
