# Phase 2 Prompts: Transitioning DaVinci Concepts to Atlas

Below are comprehensive prompts you can provide to Jules (or your LLM of choice) while working inside the `.atlas` repository. These prompts are designed to inject the successful background worker and AI Agent concepts from your older MK Dev `CDX_Automation/.davinci` system into the modern Atlas architecture.

You can paste these prompts sequentially as you tackle each domain.

---

## Prompt 1: The Email Archive & Vector Ingestion Engine

**Use this prompt to establish the Email Database and ChromaDB search capabilities.**

```markdown
I am migrating successful background workers from my legacy CDX system into this Atlas repository. The first critical piece is the Email Archiver and Vector Database. 

In my old system (`.davinci/src/email_fetcher.py` and `rebuild_vectors.py`), we fetched emails from Gmail/Outlook, stored them in SQLite, and chunked them into a ChromaDB vector database with "Concept Tagging" (Safety, Finance, HR) so the AI had historical context.

Please build the corresponding services in Atlas according to the `ARCHITECTURE.md` specifications:
1. **Email Sync Service:** Build `backend/services/sync_service.py` to fetch emails. It MUST follow the Schema rules in `ARCHITECTURE.md` (specifically, NEVER truncate `body_text` or `body_html`).
2. **Vector Ingestion:** Build `backend/services/search_service.py` utilizing ChromaDB. When emails are saved, they should be vectorized and stored in the `emails` collection with metadata (project_id, date, sender).
3. **Altimeter Linking:** Integrate the stubbed `AltimeterIntegration.link_email_to_project()` method so incoming emails are automatically tagged with their corresponding Altimeter Project ID if a match is found in the subject/body.

Provide the implementation for `sync_service.py` and `search_service.py`.
```

---

## Prompt 2: The "Morning Briefing" Aggregation Worker

**Use this prompt to rebuild the executive summary reporting engine.**

```markdown
In my previous system, I had a highly effective python background worker called `morning_briefing.py`. Its philosophy was "Collect One, Stop One" – instead of spamming PMs with every individual daily log, it woke up at 6:00 AM, aggregated all the field logs and alerts from the previous day, and sent a single concise summary.

Please implement the **Morning Briefing Generator** in Atlas:
1. **The Scheduler:** Add a cron-style job (using APScheduler or similar) to `backend/core/` that fires daily at 6:00 AM.
2. **Data Aggregation:** The worker needs to query the Altimeter database (via `AltimeterIntegration`) to pull all `DailyLogs` submitted yesterday, as well as any high-priority system alerts (e.g., from `MaterialTracking` or `Exaktime`).
3. **AI Summarization:** Pass this raw data to the `GeminiClient` with a prompt to generate a clean, executive-level "Morning Briefing" summary categorized by Project.
4. **Delivery:** Create the `backend/services/email_service.py` to dispatch this generated HTML email to michael@daviselectric.biz.

Please write the scheduled job and the Gemini summarization logic.
```

---

## Prompt 3: The Procore "Safe Mode" Drafter (DaVinci Agent)

**Use this prompt to bring the Procore automation into the Atlas Project Agent.**

```markdown
The final piece to port over is the Procore Daily Log automation. In my legacy system, the `.davinci` agent had a specific capability: "Procore Draft Generator (Safe Mode)". It would read the context of the day's work and draft a formatted Daily Log into ana draft in my outbox to myself for human review, strictly avoiding direct API write access to Procore to prevent mistakes.

Let's implement this concept into Atlas's `project_agent.py`:
1. **The Capability:** Add a tool/capability to the `ProjectAgent` that allows it to generate Procore-formatted Daily Logs based on conversational input (e.g., "Draft a log for Project X stating we finished the underground rough-in").
2. **Context Gathering:** Before drafting, the agent should search the ChromaDB vector store (via `SemanticSearch`) to pull any relevant emails or prior logs from the past 48 hours for that specific project to ensure accuracy.
3. **Safe Mode Output:** Instead of trying to POST directly to Procore or Altimeter via API, the agent should save the drafted log as a pending `Task` or `Draft` in the Atlas database, clearly flagged for the User to review, approve, and manually submit.

Please provide the updated `project_agent.py` implementing this Safe Mode drafting workflow.
```
