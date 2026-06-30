from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from agents.supervisor import SovereignSupervisor

app = FastAPI(title="Endurance CRM Agent API")

# Initialize the Supervisor
# In production, these would come from environment variables or a config file
supervisor = SovereignSupervisor(
    clinic_id="clinic_default", 
    admin_group="ADMIN_WHATSAPP_GROUP_ID", 
    dashboard_webhook="https://hooks.appsheet.com/dummy"
)

class ChatMessage(BaseModel):
    patient_phone: str
    message: str
    chat_history: Optional[List[str]] = []
    patient_data: Optional[dict] = {}

@app.post("/process")
async def process_message(chat: ChatMessage):
    try:
        # 1. Load patient profile from state (Simulated)
        # In production, this would be a DB call to Postgres
        profile = supervisor._get_state(chat.patient_phone, "profile") or chat.patient_data
        supervisor._update_state(chat.patient_phone, "profile", profile)
        
        # 2. Process through the Supervisor Loop
        result = supervisor.process_loop(
            patient_phone=chat.patient_phone, 
            message=chat.message, 
            chat_history=chat.chat_history
        )
        
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "SovereignSupervisor v1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
