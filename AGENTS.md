# Atlas Agent Blueprint (Jules Environment)

Welcome to Atlas, the "Smooth as Ice" Command Center. This file provides the architectural context and constraints for autonomous agents working within this repository.

## 🧊 The Architectural Vision

Atlas is transitioning from a Google-specific proxy to a standalone, provider-agnostic engine. Always follow the **Decoupled Architecture** patterns.

## 🏗️ Core Architecture (Communication Layer)

- **Services Factory**: [services/communication_service.py](file:///backend/services/communication_service.py) routes all requests. DO NOT import `google_service` or `imap_provider` directly in API routes. Use `comm_service`.
- **Base Class**: All new providers (e.g., Outlook, Proton) MUST inherit from the `CommunicationProvider` interface in [services/communication_provider.py](file:///backend/services/communication_provider.py).
- **Models**: Use unified fields: `remote_id` (not `gmail_id`) and `provider_type`.

## 💎 The Intelligence Bridge (Altimeter Integration)

Atlas is integrated with the Altimeter Project management database.

- Use [services/altimeter_service.py](file:///backend/services/altimeter_service.py) to fetch project context (`25-XXXX` format).
- Use `altimeter_service.get_context_for_email()` to identify mission-critical SOPs and active project phases from incoming communications.
- Asynchronous tasks in [scripts/process_tasks.py](file:///backend/scripts/process_tasks.py) should always embed "Mission Intel" (SOPs, Context) into generated Atlas Tasks.

## 🌙 The Nightly Mission

Jules is scheduled to run every night at midnight via [nightly-jules.yml](file://.github/workflows/nightly-jules.yml). During this run, it performs:

- **Daily Ingestion**: Syncs all IMAP/Google mail and bridges to Altimeter.
- **SOP Prediction**: Updates the internal Knowledge Base with newly relevant SOPs.
- **Continuous Improvement**:
  - **1:00 AM (Email)**: Audits and optimizes the communication engine and analysis prompts.
  - **2:00 AM (Tasks/Calendar)**: Refines extraction logic and implements 'Smart Deadlines'.
  - **3:00 AM (AI/Assistant)**: Conducts prompt engineering and persona alignment experiments.
- **Dynamic Prioritization**: Updates the "Current Missions" section below based on the day's communications.

## 🛠️ Current Missions for Jules

### 🟢 Completed (Last 24h)
1. **IMAP Base Sync**: Implemented robust `IMAPProvider` with UID search and date filtering.
2. **SMTP Send**: Implemented `SMTPProvider` for sending emails.
3. **Intelligence Bridge**: Enriched `process_tasks.py` with `altimeter_service` context and milestone extraction.

### 🟡 Active Priorities (Next 24h)
1. **IMAP Interactivity**: Implement `reply`, `archive`, `trash`, and `mark_unread` in `IMAPProvider`.
2. **Documentation Recovery**: Re-create `JULES_RUNBOOKS.md` to document the strategy.
3. **Frontend Wiring**: Ensure the UI (e.g., "Reply" button) triggers the new backend provider methods.
4. **Autonomous Loop**: Enhance `execute_mission.py` to support file writing or more complex actions beyond printing.

## 🛑 Critical Constraints

- **Glassmorphism**: Do not break the "Night Sky" aesthetic in the frontend. Maintain `backdrop-blur` and `bg-white/[0.02]` standards.
- **Provider-Agnostic**: All new features must work for both Google and non-Google (Standard IMAP) accounts.
- **No Direct Deletes**: Never delete email or calendar data directly from remote servers unless explicitly requested by the user.

*Stay smooth, stay autonomous.*
