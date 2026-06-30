# Endurance CRM - Clinic Onboarding SOP
# Target: Solo Developer / Operator
# Goal: Zero-Error deployment of new clinic instances

## 📋 Phase 1: Infrastructure Setup
- [ ] **Assign ID**: Create a unique `clinic_id` (e.g., `clinic_mumbai_01`).
- [ ] **DB Sharding**: 
    - Run SQL: `CREATE SCHEMA clinic_mumbai_01;`
    - Create `patient_profiles` and `chat_logs` tables within this schema.
- [ ] **Lakehouse Folder**: 
    - Create folder in MinIO: `/data/lakehouse/clinic_mumbai_01/`.

## 📋 Phase 2: Configuration & Auth
- [ ] **Google Calendar Link**:
    - Use the `google_auth_setup.py` script to authenticate the clinic's Google account.
    - Save `creds_clinic_mumbai_01.json` in the `/agents` folder.
- [ ] **Clinic Parameters**:
    - Update the `TriageProfiler` config (or DB table) with:
        - Operating Hours.
        - Pricing for core services (Cleaning, Root Canal, etc.).
        - Specialty focus.

## 📋 Phase 3: The "Golden Path" Verification
- [ ] **Test Case 1 (Triage)**: Send a message: *"I want to book"*. 
    - Verify: Bot asks for Age/Gender/Complaint.
- [ ] **Test Case 2 (Booking)**: Complete the profile.
    - Verify: Appointment appears on the Google Calendar.
- [ ] **Test Case 3 (Emergency)**: Send: *"Severe bleeding!"*.
    - Verify: Immediate alert arrives in the Admin WhatsApp group.

## 📋 Phase 4: ROI & Growth Activation
- [ ] **Sentiment Trigger**: Confirm the `GrowthExpert` is monitoring the chat.
- [ ] **Review Flow**: Trigger a "Positive" response to verify the review draft generation.
