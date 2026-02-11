# 📘 Jules Runbooks

These runbooks define the automated processes for the Atlas Nightly Mission.

## 🌙 The Nightly Cycle (Midnight Protocol)

### 1. Daily Ingestion
**Trigger**: 00:00 CST
- **Action**: `python backend/scripts/execute_mission.py --type email --prompt "Sync and analyze daily communications."`
- **Goal**: Ingest all emails from the last 24h, bridge to Altimeter, and update `task.md` context.

### 2. SOP Prediction
**Trigger**: 01:00 CST
- **Action**: `python backend/scripts/execute_mission.py --type optimization --prompt "Review recent task completions and propose new SOPs."`
- **Goal**: Identify repeated manual patterns and codify them into Standard Operating Procedures.

### 3. Continuous Improvement
**Trigger**: 02:00 CST
- **Action**: `python backend/scripts/execute_mission.py --type maintenance --prompt "Audit system performance and suggest code optimizations."`
- **Goal**: Self-healing code and prompt refinement.

## 🛠️ Manual Interventions

If the nightly cycle fails:
1. Check GitHub Actions logs.
2. Run `python backend/scripts/execute_mission.py --type maintenance` locally to diagnose.
3. Check `OVERNIGHT_LOG.md` for errors.
