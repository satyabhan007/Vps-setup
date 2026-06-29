import requests

class HITLManager:
    def __init__(self, admin_whatsapp_group):
        self.admin_group = admin_whatsapp_group

    def evaluate_confidence(self, ai_response, confidence_score):
        """
        Decides if a human needs to intervene.
        """
        if confidence_score < 0.7 or "EMERGENCY" in ai_response.upper():
            return "HUMAN_REQUIRED"
        return "AI_CONFIRMED"

    def trigger_handover(self, patient_phone, chat_history):
        """
        Alerts the clinic staff that the AI is stuck and needs a human.
        """
        alert_msg = f"⚠️ ALERT: Human intervention required for patient {patient_phone}.\n\nLast AI Response: {chat_history[-1]}"
        # Call WhatsApp API to send to the Admin Group
        return alert_msg
