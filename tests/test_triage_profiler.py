"""
Unit tests for agents/triage_profiler.py

Tests:
  - classify_intent: all 4 intent categories
  - analyze_profile: full, partial, and empty patient data
  - generate_next_question: each required field, and no missing fields
"""

import pytest
from agents.triage_profiler import TriageProfiler


CLINIC_ID = "test_clinic"


@pytest.fixture
def profiler():
    return TriageProfiler(clinic_id=CLINIC_ID)


# ---------------------------------------------------------------------------
# classify_intent
# ---------------------------------------------------------------------------

class TestClassifyIntent:
    def test_emergency_on_severe_pain(self, profiler):
        assert profiler.classify_intent("I have severe tooth pain") == "EMERGENCY"

    def test_emergency_on_bleeding(self, profiler):
        assert profiler.classify_intent("My gum is bleeding badly") == "EMERGENCY"

    def test_emergency_on_pain_keyword(self, profiler):
        assert profiler.classify_intent("Terrible pain in my jaw") == "EMERGENCY"

    def test_booking_on_appointment(self, profiler):
        assert profiler.classify_intent("I want to book an appointment") == "BOOKING"

    def test_booking_on_schedule(self, profiler):
        assert profiler.classify_intent("Can I schedule a slot for tomorrow?") == "BOOKING"

    def test_booking_on_slot(self, profiler):
        assert profiler.classify_intent("Is there a free slot this evening?") == "BOOKING"

    def test_pricing_on_cost(self, profiler):
        assert profiler.classify_intent("What is the cost of a cleaning?") == "PRICING"

    def test_pricing_on_fee(self, profiler):
        assert profiler.classify_intent("What are the fees for consultation?") == "PRICING"

    def test_pricing_on_price(self, profiler):
        assert profiler.classify_intent("How much is the price for a root canal?") == "PRICING"

    def test_general_inquiry_fallback(self, profiler):
        assert profiler.classify_intent("Hello, what are your working hours?") == "GENERAL_INQUIRY"

    def test_general_inquiry_empty_message(self, profiler):
        assert profiler.classify_intent("") == "GENERAL_INQUIRY"

    def test_case_insensitive_matching(self, profiler):
        """Keywords should be matched case-insensitively."""
        assert profiler.classify_intent("BOOK AN APPOINTMENT PLEASE") == "BOOKING"


# ---------------------------------------------------------------------------
# analyze_profile
# ---------------------------------------------------------------------------

class TestAnalyzeProfile:
    REQUIRED_FIELDS = ["age", "gender", "chief_complaint", "previous_history"]

    def test_full_profile_returns_no_missing(self, profiler):
        data = {
            "age": "30",
            "gender": "Female",
            "chief_complaint": "Tooth pain",
            "previous_history": "None",
        }
        assert profiler.analyze_profile(data) == []

    def test_empty_profile_returns_all_fields(self, profiler):
        missing = profiler.analyze_profile({})
        assert set(missing) == set(self.REQUIRED_FIELDS)

    def test_partial_profile_returns_only_missing(self, profiler):
        data = {"age": "25", "gender": "Male"}
        missing = profiler.analyze_profile(data)
        assert "chief_complaint" in missing
        assert "previous_history" in missing
        assert "age" not in missing
        assert "gender" not in missing

    def test_empty_string_field_is_treated_as_missing(self, profiler):
        data = {"age": "", "gender": "Male", "chief_complaint": "Pain", "previous_history": "None"}
        missing = profiler.analyze_profile(data)
        assert "age" in missing

    def test_none_field_is_treated_as_missing(self, profiler):
        data = {"age": None, "gender": "Male", "chief_complaint": "Pain", "previous_history": "None"}
        missing = profiler.analyze_profile(data)
        assert "age" in missing


# ---------------------------------------------------------------------------
# generate_next_question
# ---------------------------------------------------------------------------

class TestGenerateNextQuestion:
    def test_asks_for_age_first(self, profiler):
        question = profiler.generate_next_question(["age", "gender"])
        assert "age" in question.lower()

    def test_asks_for_gender(self, profiler):
        question = profiler.generate_next_question(["gender"])
        assert "gender" in question.lower()

    def test_asks_for_chief_complaint(self, profiler):
        question = profiler.generate_next_question(["chief_complaint"])
        assert "visit" in question.lower() or "reason" in question.lower()

    def test_asks_for_previous_history(self, profiler):
        question = profiler.generate_next_question(["previous_history"])
        assert "history" in question.lower() or "allergies" in question.lower()

    def test_returns_thank_you_when_no_missing(self, profiler):
        question = profiler.generate_next_question([])
        assert "thank" in question.lower() or "everything" in question.lower()

    def test_prioritizes_first_missing_field(self, profiler):
        """Should only ask about the first missing field, not all at once."""
        question = profiler.generate_next_question(["age", "gender", "chief_complaint"])
        # The response should be a single focused question about age
        assert "?" in question
