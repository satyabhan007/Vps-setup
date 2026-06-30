# 📜 Sovereign Development Log: Endurance WhatsApp CRM
**Project Focus**: Extreme Cost Efficiency & High Reliability (Sovereign Stack)
**Operator**: Solo Developer / Architect

## 🎯 The Mission
Build a high-footfall clinical automation engine that replaces "AI Wrappers" with a **Deterministic Task-Engine**. The goal is a system that is zero-maintenance for the developer and zero-friction for the clinic.

## 🏗️ Architectural Decisions & Evolution

### 1. From Linear Orchestrator $\rightarrow$ Sovereign Supervisor
- **Original**: A simple router that called agents.
- **Upgrade**: A **Multi-Expert Supervisor** implementing a `Plan $\rightarrow$ Execute $\rightarrow$ Verify` loop.
- **Reason**: Eliminates hallucinations. The Supervisor verifies if requirements (like patient profiling) are met before allowing an action (like booking).

### 2. From Volatile Memory $\rightarrow$ Persistent Sovereign State
- **Original**: In-memory Python dictionaries.
- **Upgrade**: **Postgres JSONB Session Store**.
- **Reason**: Reliability. Server restarts no longer wipe patient progress.

### 3. From Manual Ops $\rightarrow$ Self-Healing Infra
- **Original**: Manual `docker compose up` and SSH checks.
- **Upgrade**: **Dokploy CI/CD + Sovereign Watchdog + Health Monitor**.
- **Reason**: Reducing "Operational Debt." The system monitors itself and restarts automatically.

### 4. From Standard AI $\rightarrow$ The Kaizen Loop
- **Original**: Generic LLM responses.
- **Upgrade**: **MinIO Lakehouse $\rightarrow$ Golden Dataset $\rightarrow$ Tuning**.
- **Reason**: Building a "Data Moat." Every human correction becomes training data for a proprietary clinical model.

## 📉 Cost Efficiency Strategy
- **Hosting**: Hetzner/DigitalOcean India VPS ($\approx$ ₹800/mo).
- **Intelligence**: Gemini 1.5 Flash (Free Tier) used as a reasoning layer, not a database.
- **PaaS**: Dokploy (Self-hosted) instead of expensive managed services.
- **State**: PostgreSQL (Sovereign) instead of expensive managed NoSQL.

## 🛠️ Tech Stack Summary
- **Language**: Python (FastAPI, Psycopg2)
- **Logic**: n8n (Low-code Orchestration)
- **Data**: PostgreSQL (pgvector) & MinIO (S3-compatible)
- **DevOps**: Docker, Dokploy, GitHub Actions (CI/CD)
- **Communication**: WhatsApp Cloud API (Direct Meta Integration)

---
**Note**: This log serves as the "Institutional Memory" for the project. Any future developers should refer to the `SovereignSupervisor` logic and the `PROJECT_CHECKPOINT.md` for deployment.
