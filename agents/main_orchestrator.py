from agents.triage_profiler import TriageProfiler
from agents.hitl_manager import HITLManager
from agents.executor_booking import BookingExecutor

class LoopOrchestrator:
    def __init__(self, clinic_id, admin_group, dashboard_webhook=None):
        self.profiler = TriageProfiler(clinic_id)
        self.hitl = HITLManager(admin_group, dashboard_webhook)
        self.booking = BookingExecutor(clinic_id)

    def handle_message(self, patient_phone, message, patient_data=None, chat_history=None):
        """
        Main entry point for processing a WhatsApp message.
        """
        if patient_data is None: patient_data = {}
        if chat_history is None: chat_history = []
        
        # 1. Triage & Intent Classification
        intent = self.profiler.classify_intent(message)
        
        # 2. Check for Emergency/High-Priority Handover
        hitl_status = self.hitl.evaluate_confidence("", 1.0, intent) # Use intent for priority
        if hitl_status != "AI_CONFIRMED":
            return {
                "action": "HANDOVER",
                "response": self.hitl.trigger_handover(patient_phone, chat_history, reason=f"Intent: {intent}"),
                "status": hitl_status
            }

        # 3. Logic Branching based on Intent
        if intent == "BOOKING":
            # Check if we have enough profiling data before booking
            missing = self.profiler.analyze_profile(patient_data)
            if missing:
                return {
                    "action": "PROFILING",
                    "response": self.profiler.generate_next_question(missing),
                    "missing_fields": missing
                }
            # Proceed to booking logic (simplified here)
            return {
                "action": "BOOKING_PROCESS",
                "response": "I have your details. Let me check the available slots for you...",
                "agent": "executor_booking"
            }

        if intent == "PRICING":
            return {
                "action": "RESPONSE",
                "response": "Our pricing varies by treatment. I can have our coordinator send you a detailed price list. Would you like that?"
            }

        # 4. General Profiling for new users
        missing = self.profiler.analyze_profile(patient_data)
        if missing:
            return {
                "action": "PROFILING",
                "response": self.profiler.generate_next_question(missing),
                "missing_fields": missing
            }

        return {
            "action": "RESPONSE",
            "response": "I'm here to help you with your clinic visit. How can I assist you today?"
        }

# Simulation
if __name__ == "__main__":
    orch = LoopOrchestrator("clinic_123", "ADMIN_GROUP_ID", "http://webhook.site/dummy")
    
    # Test 1: Emergency
    print("Test 1 (Emergency):")
    print(orch.handle_message("91-99999", "I am bleeding heavily!"))
    
    # Test 2: Booking without data
    print("\nTest 2 (Booking - Missing Data):")
    print(orch.handle_message("91-88888", "I want to book a cleaning", patient_data={"age": "25"}))
    
    # Test 3: Booking with data
    print("\nTest 3 (Booking - Complete Data):")
    complete_data = {"age": "25", "gender": "M", "chief_complaint": "Cleaning", "previous_history": "None"}
    print(orch.handle_message("91-88888", "I want to book a cleaning", patient_data=complete_data))
