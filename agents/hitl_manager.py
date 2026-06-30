import requests
import json
from datetime import datetime

class HITLManager:
    def __init__(self, admin_whatsapp_group, dashboard_webhook=None):
        self.admin_group = admin_whatsapp_group
        self.dashboard_webhook = dashboard_webhook

    def evaluate_confidence(self, ai_response, confidence_score, intent):
        """
        Decides if a human needs to intervene based on confidence and intent.
        """
        # High priority triggers for human intervention
        if intent == "EMERGENCY":
            return "HUMAN_REQUIRED_IMMEDIATE"
        
        if confidence_score < 0.7 or "I'm not sure" in ai_response or "I apologize" in ai_response:
            return "HUMAN_REQUIRED_REVIEW"
            
        return "AI_CONFIRMED"

    def trigger_handover(self, patient_phone, chat_history, reason="Low Confidence"):
        """
        Alerts the clinic staff via WhatsApp and pushes to the HITL Dashboard.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_msg = (
            f"⚠️ *HITL ALERT* ⚠️\n"
            f"Time: {timestamp}\n"
            f"Patient: {patient_phone}\n"
            f"Reason: {reason}\n\n"
            f"Last Interaction: {chat_history[-1] if chat_history else 'No history'}\n"
            f"Action: Please take over this chat."
        )
        
        # 1. Send to Admin WhatsApp Group
        # (Integration with Meta Cloud API would go here)
        print(f"Sending WhatsApp Alert to {self.admin_group}...")
        
        # 2. Push to HITL Dashboard (e.g., AppSheet/Google Sheets via Webhook)
        if self.dashboard_webhook:
            payload = {
                "patient_phone": patient_phone,
                "timestamp": timestamp,
                "reason": reason,
                "status": "PENDING_HUMAN",
                "chat_history": chat_history
            }
            try:
                requests.post(self.dashboard_webhook, json=payload)
            except Exception as e:
                print(f"Dashboard push failed: {e}")

        return alert_msg
