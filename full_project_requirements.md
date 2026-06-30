# 📑 Project Requirements: Endurance WhatsApp CRM
**Vision**: A high-reliability, deterministic automation engine for dental and dermatology clinics to manage the patient lifecycle while maintaining extreme cost efficiency and strict data sovereignty.

---

## 🎯 1. Core Objectives
*   **Deterministic Execution**: Move away from "AI wrappers." The AI is used for reasoning; the code is used for execution (e.g., the AI decides to book, but the Python code validates the slot and writes to the calendar).
*   **Extreme Cost Efficiency**: Target total operational cost of **< ₹1,000/month**.
*   **Sovereign Infrastructure**: Total ownership of data and logic to ensure **DPDP (India) Compliance**.
*   **Solo-Operator Maintenance**: The system must be "self-healing" to reduce the burden on a single developer.

---

## 🏗️ 2. Technical Requirements (The Sovereign Stack)

### A. Infrastructure Layer
*   **Deployment**: Self-hosted on a VPS (India Region) using **Dokploy/Coolify**.
*   **Orchestration**: **n8n** (Self-hosted) for workflow management and API routing.
*   **Database**: **PostgreSQL with pgvector** for persistent patient state and RAG-based memory.
*   **Lakehouse**: **MinIO (S3-compatible)** for storing raw chat logs and the "Golden Dataset".
*   **Communication**: Direct integration with **WhatsApp Cloud API (Meta)**.

### B. Intelligence Layer (The Supervisor Architecture)
The system must implement a **Multi-Expert Supervisor Loop** (Plan $\rightarrow$ Execute $\rightarrow$ Verify):
1.  **Triage Expert**: Must classify intents (Emergency, Booking, Pricing, General) and ensure a "Golden Profile" (Age, Gender, Complaint, History) is collected before any booking.
2.  **Booking Expert**: Must perform deterministic checks against **Google Calendar API** and execute bookings without hallucinations.
3.  **HITL Manager (Human-In-The-Loop)**: Must trigger immediate alerts to clinic staff for `EMERGENCY` intents or low-confidence AI responses.
4.  **Growth Expert**: Must detect "peak satisfaction" markers and generate personalized, SEO-optimized Google review drafts.
5.  **Kaizen Expert**: Must log every interaction to the Lakehouse and filter human-corrected chats to create a training set for model tuning.

---

## 🚀 3. Functional Requirements

### Requirement 1: WhatsApp Optimization
*   **Deterministic Booking**: No "guessing" slots. AI extracts intent $\rightarrow$ Code validates slot $\rightarrow$ Code books.
*   **Profiling Loop**: If data is missing, the bot must politely loop back to the patient to collect missing profile fields.

### Requirement 2: Zero-Friction Onboarding
*   **AI-Led Profiling**: Clinics must be able to onboard by having the AI collect their operating hours, pricing, and specialties via chat.
*   **One-Click Auth**: Integration with Google OAuth for immediate Calendar and Email access.

### Requirement 3: Review & ROI Engine
*   **Sentiment Trigger**: Automatically detect when a patient is happy and nudge them toward a review.
*   **ROI Reporting**: Track a hard metric: **"Empty Slots Filled"** vs. **"No-Show Reduction"** to prove value to the clinic owner.

### Requirement 4: The Kaizen Loop (Data Moat)
*   **Interaction Logging**: Every turn must be stored in MinIO.
*   **Human-Correction Filtering**: Identify chats where staff corrected the AI to create a "Golden Dataset" for future fine-tuning on Vertex AI.

---

## 🛡️ 4. Reliability & Compliance Requirements

### A. DPDP India Compliance
*   **Data Residency**: All PII (Personally Identifiable Information) must stay on Indian servers.
*   **Isolation**: Multi-tenant architecture using `clinic_id` sharding in Postgres.
*   **Consent**: Mandatory opt-in flow at the start of every interaction.

### B. "Solo-Dev" Reliability (The Self-Healing Layer)
*   **Sovereign Watchdog**: Automatic container restarts if the API health check fails.
*   **Persistent Memory**: All session states must be stored in Postgres (no volatile memory).
*   **SOPs**: Detailed Markdown playbooks for onboarding and incident response.
*   **Automated Backups**: Scheduled snapshots of DB and Lakehouse.

---

## 💰 5. Cost Target (Monthly Estimate)
| Item | Budget (INR) | Note |
| :--- | :--- | :--- |
| VPS (4vCPU, 8GB RAM) | ₹600 - ₹800 | Hetzner / DigitalOcean India |
| Domain/SSL | ₹50 | Amortized via Dokploy |
| AI Inference | ₹0 - ₹100 | Gemini 1.5 Flash Free Tier |
| **Total** | **$\approx$ ₹900** | **Target: < ₹1,000** |
