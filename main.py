from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import os
from agents.supervisor import SovereignSupervisor

app = FastAPI(title="Endurance CRM Agent API")

# Initialize the Supervisor from environment variables
supervisor = SovereignSupervisor(
    clinic_id=os.getenv("CLINIC_ID", "clinic_default"),
    admin_group=os.getenv("ADMIN_GROUP", "ADMIN_WHATSAPP_GROUP_ID"),
    dashboard_webhook=os.getenv("DASHBOARD_WEBHOOK", "https://hooks.appsheet.com/dummy")
)

class ChatMessage(BaseModel):
    patient_phone: str
    message: str
    chat_history: Optional[List[str]] = []
    patient_data: Optional[dict] = {}

@app.post("/process")
async def process_message(chat: ChatMessage):
    try:
        # Merge any inline patient_data into persistent state first
        if chat.patient_data:
            existing = supervisor._get_state(chat.patient_phone)
            merged = {**existing, "profile": {**existing.get("profile", {}), **chat.patient_data}}
            supervisor._update_state(chat.patient_phone, merged)

        # Process through the Supervisor Loop (Plan → Execute → Verify)
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
