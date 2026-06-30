import json
import datetime

class KaizenExpert:
    def __init__(self, clinic_id):
        self.clinic_id = clinic_id
        self.lakehouse_path = f"/data/lakehouse/{clinic_id}/"

    def log_interaction(self, patient_phone, message, ai_response, metadata):
        """
        Saves raw interaction to MinIO Lakehouse.
        """
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "patient": patient_phone,
            "user_msg": message,
            "ai_res": ai_response,
            "metadata": metadata
        }
        # In production, this uses a MinIO client to upload a JSON file
        print(f"📝 Kaizen: Logging interaction to {self.lakehouse_path}")
        return True

    def identify_golden_dataset(self, interaction_logs):
        """
        Filters chats where staff corrected the AI to create a tuning set.
        """
        golden_set = []
        for log in interaction_logs:
            if log.get("staff_corrected") == True:
                golden_set.append({
                    "input": log["user_msg"],
                    "wrong_ai_response": log["ai_res"],
                    "correct_human_response": log["human_correction"]
                })
        return golden_set

    def suggest_tuning_parameters(self, golden_set):
        """
        Analyzes common failures to suggest LLM system prompt updates.
        """
        if not golden_set:
            return "No tuning needed yet."
        
        return f"Found {len(golden_set)} correction patterns. Suggesting update to 'Triage' prompt to handle these cases."

# Example usage
if __name__ == "__main__":
    kaizen = KaizenExpert("clinic_123")
    kaizen.log_interaction("91-999", "Hello", "Hi there!", {"intent": "greeting"})
    
    logs = [
        {"user_msg": "Price?", "ai_res": "I don't know", "staff_corrected": True, "human_correction": "The cleaning starts at 500 INR."}
    ]
    golden = kaizen.identify_golden_dataset(logs)
    print(f"Golden Set size: {len(golden)}")
    print(kaizen.suggest_tuning_parameters(golden))
