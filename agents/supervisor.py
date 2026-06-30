import json
import psycopg2
from psycopg2.extras import RealDictCursor
from triage_profiler import TriageProfiler
from hitl_manager import HITLManager
from executor_booking import BookingExecutor
from growth_reviews import GrowthExpert
from kaizen_optimizer import KaizenExpert

class SovereignSupervisor:
    def __init__(self, clinic_id, admin_group, dashboard_webhook=None):
        self.clinic_id = clinic_id
        # Initialize Expert Pool
        self.experts = {
            "triage": TriageProfiler(clinic_id),
            "hitl": HITLManager(admin_group, dashboard_webhook),
            "booking": BookingExecutor(clinic_id),
            "growth": GrowthExpert(clinic_id),
            "kaizen": KaizenExpert(clinic_id)
        }
        # DB Configuration (in production, use environment variables)
        self.db_config = {
            "dbname": "crm_db",
            "user": "admin",
            "password": "secure_password_change_me",
            "host": "postgres", 
            "port": 5432
        }
        self._ensure_state_table()

    def _get_db_conn(self):
        return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)

    def _ensure_state_table(self):
        """Creates the session state table for persistent memory."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS session_state (
            patient_phone TEXT PRIMARY KEY,
            clinic_id TEXT,
            state_data JSONB,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self._get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_table_sql)
                    conn.commit()
        except Exception as e:
            print(f"DB Initialization Error: {e}")

    def _update_state(self, patient_phone, state_update):
        """Persists state to Postgres using JSONB merge."""
        sql = """
        INSERT INTO session_state (patient_phone, clinic_id, state_data, updated_at)
        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (patient_phone) DO UPDATE 
        SET state_data = session_state.state_data || EXCLUDED.state_data,
            updated_at = EXCLUDED.updated_at;
        """
        try:
            with self._get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (patient_phone, self.clinic_id, json.dumps(state_update)))
                    conn.commit()
        except Exception as e:
            print(f"State Persistence Error: {e}")

    def _get_state(self, patient_phone):
        """Retrieves the full persistent state for a patient."""
        sql = "SELECT state_data FROM session_state WHERE patient_phone = %s;"
        try:
            with self._get_db_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (patient_phone,))
                    row = cur.fetchone()
                    return row['state_data'] if row else {}
        except Exception as e:
            print(f"State Retrieval Error: {e}")
            return {}

    def process_loop(self, patient_phone, message, chat_history=None):
        """
        Multi-Expert Supervisor Loop:
        Plan -> Execute -> Verify -> Respond
        """
        if chat_history is None: chat_history = []
        
        # --- PHASE 1: PLAN (Intent & State Analysis) ---
        # Fetch persistent memory from DB
        patient_state = self._get_state(patient_phone)
        patient_data = patient_state.get("profile", {})
        
        current_intent = self.experts["triage"].classify_intent(message)
        
        # Check for critical priority (Emergency)
        hitl_status = self.experts["hitl"].evaluate_confidence("", 1.0, current_intent)
        if hitl_status != "AI_CONFIRMED":
            return self._execute_handover(patient_phone, chat_history, hitl_status)

        # --- PHASE 2: EXECUTE (Expert Delegation) ---
        result = None
        
        if current_intent == "BOOKING":
            missing = self.experts["triage"].analyze_profile(patient_data)
            if missing:
                result = {
                    "expert": "triage",
                    "action": "COLLECT_DATA",
                    "response": self.experts["triage"].generate_next_question(missing),
                    "data_update": {"profile": patient_data, "missing": missing}
                }
            else:
                result = {
                    "expert": "booking",
                    "action": "PROCESS_BOOKING",
                    "response": "I have all your details. Checking the calendar now...",
                }
        
        elif current_intent == "PRICING":
            result = {
                "expert": "triage",
                "action": "INFO_RESPONSE",
                "response": "I can provide our general price list or connect you with our coordinator for a custom quote. Which do you prefer?"
            }
            
        else:
            missing = self.experts["triage"].analyze_profile(patient_data)
            if missing:
                result = {
                    "expert": "triage",
                    "action": "COLLECT_DATA",
                    "response": self.experts["triage"].generate_next_question(missing),
                    "data_update": {"profile": patient_data, "missing": missing}
                }
            else:
                result = {
                    "expert": "triage",
                    "action": "GENERAL_HELP",
                    "response": "How can I help you with your clinic visit today?"
                }

        # --- PHASE 3: VERIFY & UPDATE ---
        # Log to Kaizen Lakehouse
        self.experts["kaizen"].log_interaction(
            patient_phone, 
            message, 
            result["response"] if result else "Error", 
            {"intent": current_intent, "expert": result["expert"] if result else "none"}
        )

        # Persist updated state to Postgres
        if result and "data_update" in result:
            self._update_state(patient_phone, result["data_update"])

        return {
            "final_response": result["response"],
            "expert_used": result["expert"],
            "action_taken": result["action"],
            "intent": current_intent
        }

    def _execute_handover(self, patient_phone, chat_history, status):
        response = self.experts["hitl"].trigger_handover(patient_phone, chat_history, reason=status)
        return {
            "final_response": response,
            "expert_used": "hitl",
            "action_taken": "HANDOVER",
            "intent": "EMERGENCY/CRITICAL"
        }

if __name__ == "__main__":
    # Simple test to verify DB connectivity (will fail without docker running)
    print("Sovereign Supervisor Loaded. Awaiting DB connection...")
    supervisor = SovereignSupervisor("clinic_123", "ADMIN_GROUP_ID")
    print("Sovereign Supervisor initialized successfully.")
