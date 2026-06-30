import json

class TriageProfiler:
    def __init__(self, clinic_id):
        self.clinic_id = clinic_id
        self.required_fields = ["age", "gender", "chief_complaint", "previous_history"]

    def classify_intent(self, message):
        """
        Classifies the user message into a category.
        In a real scenario, this would call Gemini 1.5 Flash.
        """
        msg = message.lower()
        if any(word in msg for word in ["pain", "emergency", "bleeding", "severe"]):
            return "EMERGENCY"
        if any(word in msg for word in ["book", "appointment", "schedule", "slot"]):
            return "BOOKING"
        if any(word in msg for word in ["price", "cost", "charge", "fee"]):
            return "PRICING"
        return "GENERAL_INQUIRY"

    def analyze_profile(self, patient_data):
        """
        Checks which required fields are missing from the patient profile.
        """
        missing = [field for field in self.required_fields if field not in patient_data or not patient_data[field]]
        return missing

    def generate_next_question(self, missing_fields):
        """
        Generates a polite question to collect the next piece of information.
        """
        if not missing_fields:
            return "Thank you for the details. I have everything I need to help the doctor prepare for your visit."
        
        field = missing_fields[0]
        questions = {
            "age": "Could you please tell me your age?",
            "gender": "May I know your gender?",
            "chief_complaint": "Could you describe the main reason for your visit today?",
            "previous_history": "Do you have any previous medical history or allergies we should be aware of?"
        }
        return questions.get(field, f"Could you please provide your {field}?")

# Example usage for n8n integration
if __name__ == "__main__":
    profiler = TriageProfiler(clinic_id="clinic_123")
    
    # Simulate a chat
    user_msg = "I have severe tooth pain and want to book an appointment"
    intent = profiler.classify_intent(user_msg)
    print(f"Intent: {intent}")
    
    current_data = {"age": "30"}
    missing = profiler.analyze_profile(current_data)
    print(f"Missing: {missing}")
    
    next_q = profiler.generate_next_question(missing)
    print(f"Next Question: {next_q}")
