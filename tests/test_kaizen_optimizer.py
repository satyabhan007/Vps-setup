"""
Unit tests for agents/kaizen_optimizer.py

Tests:
  - log_interaction: returns True, correct path used
  - identify_golden_dataset: filters staff_corrected=True entries only
  - suggest_tuning_parameters: handles empty set and non-empty set
"""

import pytest
from agents.kaizen_optimizer import KaizenExpert


CLINIC_ID = "test_clinic"
PATIENT_PHONE = "+919876543210"


@pytest.fixture
def kaizen():
    return KaizenExpert(clinic_id=CLINIC_ID)


# ---------------------------------------------------------------------------
# log_interaction
# ---------------------------------------------------------------------------

class TestLogInteraction:
    def test_returns_true_on_success(self, kaizen):
        result = kaizen.log_interaction(
            patient_phone=PATIENT_PHONE,
            message="Hello",
            ai_response="Hi there!",
            metadata={"intent": "GENERAL_INQUIRY"},
        )
        assert result is True

    def test_lakehouse_path_contains_clinic_id(self, kaizen):
        """Verify the clinic-specific path is used for isolation."""
        assert CLINIC_ID in kaizen.lakehouse_path

    def test_does_not_raise_with_empty_metadata(self, kaizen):
        result = kaizen.log_interaction(PATIENT_PHONE, "msg", "response", {})
        assert result is True

    def test_does_not_raise_with_complex_metadata(self, kaizen):
        metadata = {"intent": "BOOKING", "expert": "triage", "confidence": 0.9}
        result = kaizen.log_interaction(PATIENT_PHONE, "book me", "sure", metadata)
        assert result is True


# ---------------------------------------------------------------------------
# identify_golden_dataset
# ---------------------------------------------------------------------------

class TestIdentifyGoldenDataset:
    def test_filters_only_staff_corrected_entries(self, kaizen):
        logs = [
            {
                "user_msg": "Price?",
                "ai_res": "I don't know",
                "staff_corrected": True,
                "human_correction": "Cleaning starts at ₹500.",
            },
            {
                "user_msg": "Book appointment",
                "ai_res": "Confirmed!",
                "staff_corrected": False,
            },
        ]
        golden = kaizen.identify_golden_dataset(logs)
        assert len(golden) == 1
        assert golden[0]["input"] == "Price?"
        assert golden[0]["correct_human_response"] == "Cleaning starts at ₹500."

    def test_empty_logs_returns_empty_list(self, kaizen):
        assert kaizen.identify_golden_dataset([]) == []

    def test_no_corrections_returns_empty_list(self, kaizen):
        logs = [{"user_msg": "Hi", "ai_res": "Hello", "staff_corrected": False}]
        assert kaizen.identify_golden_dataset(logs) == []

    def test_all_corrections_returns_all(self, kaizen):
        logs = [
            {
                "user_msg": f"Q{i}",
                "ai_res": f"wrong_{i}",
                "staff_corrected": True,
                "human_correction": f"correct_{i}",
            }
            for i in range(5)
        ]
        golden = kaizen.identify_golden_dataset(logs)
        assert len(golden) == 5

    def test_golden_entry_has_required_keys(self, kaizen):
        logs = [
            {
                "user_msg": "Fee?",
                "ai_res": "Unknown",
                "staff_corrected": True,
                "human_correction": "₹700.",
            }
        ]
        entry = kaizen.identify_golden_dataset(logs)[0]
        assert "input" in entry
        assert "wrong_ai_response" in entry
        assert "correct_human_response" in entry

    def test_missing_staff_corrected_key_is_excluded(self, kaizen):
        """Entries without staff_corrected key should not raise and should be excluded."""
        logs = [{"user_msg": "Hi", "ai_res": "Hello"}]
        result = kaizen.identify_golden_dataset(logs)
        assert result == []


# ---------------------------------------------------------------------------
# suggest_tuning_parameters
# ---------------------------------------------------------------------------

class TestSuggestTuningParameters:
    def test_empty_golden_set_returns_no_tuning_needed(self, kaizen):
        result = kaizen.suggest_tuning_parameters([])
        assert "no tuning" in result.lower()

    def test_non_empty_set_returns_count_in_suggestion(self, kaizen):
        golden = [
            {"input": "Q", "wrong_ai_response": "W", "correct_human_response": "C"}
        ] * 3
        result = kaizen.suggest_tuning_parameters(golden)
        assert "3" in result

    def test_non_empty_set_suggests_prompt_update(self, kaizen):
        golden = [{"input": "Q", "wrong_ai_response": "W", "correct_human_response": "C"}]
        result = kaizen.suggest_tuning_parameters(golden)
        # Should mention some update suggestion
        assert len(result) > 10
