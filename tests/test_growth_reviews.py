"""
Unit tests for agents/growth_reviews.py (GrowthExpert)

Tests:
  - analyze_sentiment: POSITIVE (≥2 markers), NEUTRAL (<2 markers)
  - generate_review_draft: returns None for NEUTRAL, string for POSITIVE
  - calculate_roi: correct revenue, no-show rate, status
"""

import pytest
from agents.growth_reviews import GrowthExpert


CLINIC_ID = "test_clinic"


@pytest.fixture
def growth():
    return GrowthExpert(clinic_id=CLINIC_ID)


# ---------------------------------------------------------------------------
# analyze_sentiment
# ---------------------------------------------------------------------------

class TestAnalyzeSentiment:
    def test_positive_with_two_markers(self, growth):
        history = ["Thank you so much!", "The treatment was amazing."]
        assert growth.analyze_sentiment(history) == "POSITIVE"

    def test_positive_with_multiple_markers(self, growth):
        history = ["Absolutely great!", "Best clinic ever. Perfect results, thank you!"]
        assert growth.analyze_sentiment(history) == "POSITIVE"

    def test_neutral_with_one_marker(self, growth):
        history = ["Thank you", "The wait was a bit long."]
        assert growth.analyze_sentiment(history) == "NEUTRAL"

    def test_neutral_with_no_markers(self, growth):
        history = ["How long will this take?", "Okay."]
        assert growth.analyze_sentiment(history) == "NEUTRAL"

    def test_neutral_with_empty_history(self, growth):
        assert growth.analyze_sentiment([]) == "NEUTRAL"

    def test_case_insensitive_marker_detection(self, growth):
        history = ["THANK YOU", "AMAZING experience"]
        assert growth.analyze_sentiment(history) == "POSITIVE"

    def test_single_message_with_multiple_markers(self, growth):
        history = ["Great visit! Thank you, it was perfect and helpful!"]
        assert growth.analyze_sentiment(history) == "POSITIVE"


# ---------------------------------------------------------------------------
# generate_review_draft
# ---------------------------------------------------------------------------

class TestGenerateReviewDraft:
    def test_returns_none_for_neutral_sentiment(self, growth):
        assert growth.generate_review_draft("Ravi", "Cleaning", "NEUTRAL") is None

    def test_returns_string_for_positive_sentiment(self, growth):
        draft = growth.generate_review_draft("Priya", "Root Canal", "POSITIVE")
        assert isinstance(draft, str)
        assert len(draft) > 0

    def test_draft_contains_treatment_name(self, growth):
        draft = growth.generate_review_draft("Anita", "whitening", "POSITIVE")
        assert "whitening" in draft

    def test_draft_is_non_empty_positive_text(self, growth):
        draft = growth.generate_review_draft("Suresh", "Cleaning", "POSITIVE")
        # Draft should sound positive
        assert any(word in draft.lower() for word in ["amazing", "best", "happy", "recommend", "friendly"])


# ---------------------------------------------------------------------------
# calculate_roi
# ---------------------------------------------------------------------------

class TestCalculateROI:
    def test_revenue_gain_calculation(self, growth):
        result = growth.calculate_roi(empty_slots_filled=5, no_show_reduction_rate=20)
        assert result["revenue_gain"] == 5 * 2000  # 10000 INR

    def test_zero_slots_gives_zero_revenue(self, growth):
        result = growth.calculate_roi(empty_slots_filled=0, no_show_reduction_rate=10)
        assert result["revenue_gain"] == 0

    def test_no_show_rate_in_result(self, growth):
        result = growth.calculate_roi(empty_slots_filled=3, no_show_reduction_rate=25)
        assert "25%" in result["no_show_improvement"]

    def test_status_is_high_roi(self, growth):
        result = growth.calculate_roi(empty_slots_filled=10, no_show_reduction_rate=30)
        assert result["status"] == "HIGH_ROI"

    def test_result_has_all_required_keys(self, growth):
        result = growth.calculate_roi(empty_slots_filled=1, no_show_reduction_rate=5)
        assert "revenue_gain" in result
        assert "no_show_improvement" in result
        assert "status" in result
