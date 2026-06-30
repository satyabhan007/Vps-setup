import random

class GrowthExpert:
    def __init__(self, clinic_id):
        self.clinic_id = clinic_id

    def analyze_sentiment(self, chat_history):
        """
        Detects peak satisfaction markers in the conversation.
        """
        text = " ".join([msg for msg in chat_history]).lower()
        positive_markers = ["thank you", "amazing", "great", "helpful", "fixed", "perfect", "best"]
        
        score = sum(1 for marker in positive_markers if marker in text)
        return "POSITIVE" if score >= 2 else "NEUTRAL"

    def generate_review_draft(self, patient_name, treatment, sentiment):
        """
        Creates a personalized, SEO-friendly review draft.
        """
        if sentiment != "POSITIVE":
            return None

        templates = [
            f"I had an amazing experience at the clinic for my {treatment}! Dr. was very professional. Highly recommend!",
            f"Best dental care in town. The {treatment} process was seamless and painless. Thank you!",
            f"Very happy with the results of my {treatment}. The staff is incredibly friendly and the clinic is spotless."
        ]
        return random.choice(templates)

    def calculate_roi(self, empty_slots_filled, no_show_reduction_rate):
        """
        Calculates the hard ROI for the clinic owner.
        """
        avg_visit_value = 2000 # INR
        revenue_gain = empty_slots_filled * avg_visit_value
        return {
            "revenue_gain": revenue_gain,
            "no_show_improvement": f"{no_show_reduction_rate}%",
            "status": "HIGH_ROI"
        }

# Example usage
if __name__ == "__main__":
    growth = GrowthExpert("clinic_123")
    history = ["Thank you so much for the help", "The treatment was amazing"]
    sentiment = growth.analyze_sentiment(history)
    print(f"Sentiment: {sentiment}")
    print(f"Draft: {growth.generate_review_draft('John', 'Root Canal', sentiment)}")
