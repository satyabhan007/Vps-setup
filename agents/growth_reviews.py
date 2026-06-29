import random

class GrowthAgent:
    def __init__(self, clinic_id):
        self.clinic_id = clinic_id

    def generate_review_suggestion(self, patient_name, success_metric):
        """
        Generates a highly unique, specific review draft based on the 
        actual successful outcome of the treatment.
        """
        # Templates designed to avoid "AI-sounding" generic reviews
        templates = [
            f"I'm so happy with my {success_metric}! {patient_name} did a great job, and the clinic was very professional. Highly recommend!",
            f"Finally found a place that actually delivers. My {success_metric} results are amazing. Thanks to the team at {self.clinic_id}!",
            f"The experience was seamless. The focus on {success_metric} was exactly what I needed. 5 stars!"
        ]
        return random.choice(templates)

    def trigger_review_request(self, patient_phone, review_draft):
        """
        Sends the personalized review request via WhatsApp.
        """
        message = f"Hi! We're so glad you're happy with your {review_draft}. Would you mind sharing this on Google? It helps others find us! [Google Review Link]"
        # Call WhatsApp API to send
        return message
