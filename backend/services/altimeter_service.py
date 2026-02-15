import re
import sqlite3
import os
from urllib.request import pathname2url
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.config import settings

class AltimeterService:
    """
    Service for interacting with the Altimeter business logic database.
    Provides project context, milestones, and active phases.
    """
    def __init__(self, api_base_url: str = "http://127.0.0.1:4203"):
        self.api_base_url = api_base_url
        # Robust path resolution
        alt_path = settings.ALTIMETER_PATH
        if not alt_path or not os.path.exists(alt_path):
            # Fallback to standard location if settings fail
            alt_path = os.path.join(os.path.expanduser("~"), ".altimeter")
            
        self.db_path = os.path.join(alt_path, "database", "altimeter.db")

    def _get_db_conn(self, readonly: bool = False):
        """Get a direct connection to the Altimeter database."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Altimeter database not found at {self.db_path}")

        if readonly:
            # Use URI mode to enforce read-only at the database engine level
            # file:/absolute/path/to/database?mode=ro
            try:
                abs_path = os.path.abspath(self.db_path)
                db_uri = f"file:{pathname2url(abs_path)}?mode=ro"
                conn = sqlite3.connect(db_uri, uri=True, timeout=5)
            except Exception as e:
                # Fallback if URI fails (though it shouldn't on supported versions)
                conn = sqlite3.connect(self.db_path, timeout=5)
        else:
            conn = sqlite3.connect(self.db_path, timeout=5)

        conn.row_factory = sqlite3.Row
        return conn

    def check_health(self) -> Dict[str, Any]:
        """Check connection to Altimeter DB and correct schema."""
        try:
            if not os.path.exists(self.db_path):
                 return {"status": "error", "details": f"Database file missing at {self.db_path}"}
                 
            conn = self._get_db_conn()
            # Basic connection test
            conn.execute("PRAGMA quick_check").fetchone()
            # Project check
            count = conn.execute("SELECT count(*) FROM projects WHERE is_active = 1").fetchone()[0]
            conn.close()
            return {"status": "connected", "active_projects": count}
        except Exception as e:
            return {"status": "error", "details": str(e)}

    def parse_email_for_project(self, content: str, body: str = "") -> Dict[str, Any]:
        """Extracts Altimeter-specific metadata from email content (subject + body)."""
        # Combine subject and body for analysis
        full_content = (content + "\n" + body).lower()
        
        # Project IDs (Standard Altimeter Format: 25-XXXX or 24-XXXX)
        project_ids = re.findall(r"\b(2[4-9]-\d{4})\b", full_content, re.IGNORECASE)
        
        urgency_keywords = ["urgent", "asap", "emergency", "critical", "immediately"]
        doc_keywords = ["rfi", "submittal", "change order", "drawing", "spec", "plan"]
        proposal_keywords = [
            "request for proposal", "rfp", "bid invitation", "invitation to bid", 
            "pricing request", "quote request", "addendum", "bid date", "bid due", "bids are due"
        ]
        daily_log_keywords = ["daily log", "field report", "site report", "daily report", "superintendent report"]
        
        is_urgent = any(k in full_content for k in urgency_keywords)
        found_docs = [k for k in doc_keywords if k in full_content]
        is_proposal = any(k in full_content for k in proposal_keywords)
        is_daily_log = any(k in full_content for k in daily_log_keywords)
        
        # Date Extraction for Milestones
        # Matches: "due by 2/20", "deadline 2024-05-01", "bid date 12/15"
        date_patterns = [
            r"(?:due|deadline|bid date|complete)(?:\s+(?:by|on|date|for))?[\s:]+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)",
            r"(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?) (?:deadline|due date)"
        ]

        suggested_milestones = []
        for pattern in date_patterns:
            matches = re.findall(pattern, full_content, re.IGNORECASE)
            for date_str in matches:
                suggested_milestones.append({
                    "date_text": date_str,
                    "source_context": "Found in email body"
                })

        return {
            "project_ids": list(set(project_ids)),
            "is_urgent": is_urgent,
            "doc_types": found_docs,
            "is_proposal": is_proposal,
            "is_daily_log": is_daily_log,
            "suggested_milestones": suggested_milestones
        }

    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetches project details directly from the Altimeter DB."""
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()
            # Try both UUID and Altimeter Project ID
            cursor.execute("""
                SELECT * FROM projects 
                WHERE altimeter_project_id = ? OR id = ?
            """, (project_id, project_id))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            return None

    def get_context_for_email(self, sender: str, subject: str, body: str = "") -> Dict[str, Any]:
        """Get project and contact context for an email."""
        context = {
            "project": None,
            "company_role": "Unknown",
            "file_context": "",
            "is_proposal": False,
            "is_daily_log": False
        }

        parsed = self.parse_email_for_project(subject, body)
        context["is_proposal"] = parsed["is_proposal"]
        context["is_daily_log"] = parsed["is_daily_log"]
        context["suggested_milestones"] = parsed["suggested_milestones"]

        if parsed["project_ids"]:
            project_id = parsed["project_ids"][0]
            project = self.get_project_details(project_id)
            if project:
                context["project"] = {
                    "number": project.get("altimeter_project_id"),
                    "name": project.get("name"),
                    "status": project.get("status"),
                    "customer": self._get_customer_name(project.get("customer_id"))
                }

        # Identify sender role
        try:
            email_addr = sender
            if '<' in sender:
                email_addr = sender.split('<')[1].rstrip('>')
            
            contact_info = self._get_contact_info(email_addr)
            if contact_info:
                context["company_role"] = f"{contact_info.get('role', 'Contact')} at {contact_info.get('company', 'Unknown')}"
        except Exception as e:
            pass

        # Get file context
        if context["project"]:
            context["file_context"] = self._get_recent_activity_context(context["project"]["number"])
        
        # PROACTIVE BRIDGE: Predict Mission Intel for the identified project context
        if context["project"]:
             active_phases = self.get_active_phases()
             # Filter phases for this specific project
             project_phases = [p for p in active_phases if p['project_id'] == context['project']['number']]
             if project_phases:
                 context["mission_intel"] = intelligence_bridge.predict_mission_intel(project_phases)
             else:
                 context["mission_intel"] = []
        else:
             context["mission_intel"] = []

        return context

    def _get_customer_name(self, customer_id: Optional[int]) -> str:
        if not customer_id:
            return "Unknown"
        try:
            conn = self._get_db_conn()
            row = conn.execute("SELECT company_name FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
            conn.close()
            return row['company_name'] if row else "Unknown"
        except:
            return "Unknown"

    def _get_contact_info(self, email: str) -> Optional[Dict[str, str]]:
        try:
            conn = self._get_db_conn()
            # Check employees first
            row = conn.execute("SELECT role, 'Davis Electric' as company FROM employees WHERE email = ?", (email,)).fetchone()
            if not row:
                # Then check customers
                row = conn.execute("SELECT 'Client' as role, company_name as company FROM customers WHERE email = ?", (email,)).fetchone()
            conn.close()
            return dict(row) if row else None
        except:
            return None

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects directly from Altimeter DB."""
        try:
            conn = self._get_db_conn()
            projects = conn.execute("SELECT * FROM projects WHERE is_active = 1 ORDER BY updated_at DESC").fetchall()
            conn.close()
            return [dict(p) for p in projects]
        except Exception as e:
            return []

    def get_db_schema(self, strata_level: int = 1) -> str:
        """
        Returns a read-only schema representation filtered by Strata Level.
        Allows the LLM to write SQL queries safely.
        """
        try:
            conn = self._get_db_conn()
            cursor = conn.cursor()

            # Fetch all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            schema_str = "Database Schema:\n"

            # Permission Logic (Simple)
            # Strata 1-2: Ops only (Tasks, Projects, Inventory)
            # Strata 3-4: + Financials (if exists)
            # Strata 5: All (including system tables)

            allowed_tables = tables
            if strata_level < 5:
                allowed_tables = [t for t in tables if t not in ['users', 'secrets', 'audit_logs']]
            if strata_level < 3:
                # Filter 'financ' (financials), 'money', 'budget', 'salary'
                restricted = ['financ', 'money', 'budget', 'salary']
                allowed_tables = [t for t in allowed_tables if not any(r in t for r in restricted)]

            for table in allowed_tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [f"{row[1]} ({row[2]})" for row in cursor.fetchall()]
                schema_str += f"- Table '{table}': {', '.join(columns)}\n"

            conn.close()
            return schema_str
        except Exception as e:
            return f"Error fetching schema: {e}"

    def execute_read_only_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a SQL query strictly for READ access.
        Safeguarded against modification keywords.
        """
        # 1. Safety Check
        forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
        if any(word in query.upper() for word in forbidden):
            raise ValueError("Security Alert: Modification queries are strictly forbidden.")

        try:
            conn = self._get_db_conn(readonly=True)
            cursor = conn.cursor()
            cursor.execute(query)

            # Fetch column names
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            result = [dict(zip(columns, row)) for row in rows]
            conn.close()
            return result
        except Exception as e:
            return [{"error": str(e)}]

    def get_upcoming_milestones(self, days: int = 14) -> List[Dict[str, Any]]:
        """Fetch upcoming milestones from Altimeter projects."""
        try:
            conn = self._get_db_conn()
            # Join project_phases with projects
            query = """
                SELECT ph.*, p.altimeter_project_id, p.name as project_name 
                FROM project_phases ph
                JOIN projects p ON ph.project_id = p.id
                WHERE ph.completion_date >= date('now')
                AND ph.completion_date <= date('now', '+' || ? || ' days')
                AND ph.status != 'Completed'
                ORDER BY ph.completion_date ASC
            """
            rows = conn.execute(query, (days,)).fetchall()
            conn.close()
            
            res = []
            for r in rows:
                res.append({
                    "id": f"phase-{r['id']}",
                    "title": f"{r['project_name']} - PHASE: {r['phase']}",
                    "due_date": r['completion_date'],
                    "altimeter_project_id": r['altimeter_project_id'],
                    "project_name": r['project_name']
                })
            return res
        except Exception as e:
            return []

    def get_active_phases(self) -> List[Dict[str, Any]]:
        """
        Fetch currently active phases (Start <= TODAY <= Complete).
        Used by the Oracle Protocol to predict needed SOPs.
        """
        try:
            conn = self._get_db_conn()
            # Assuming project_phases has start_date and completion_date
            query = """
                SELECT ph.*, p.altimeter_project_id, p.name as project_name
                FROM project_phases ph
                JOIN projects p ON ph.project_id = p.id
                WHERE ph.start_date <= date('now')
                AND ph.completion_date >= date('now')
                AND ph.status != 'Completed'
                ORDER BY ph.completion_date ASC
            """
            rows = conn.execute(query).fetchall()
            conn.close()

            res = []
            for r in rows:
                res.append({
                    "id": f"phase-{r['id']}",
                    "phase_name": r['phase'],
                    "project_id": r['altimeter_project_id'],
                    "project_name": r['project_name'],
                    "start_date": r['start_date'],
                    "completion_date": r['completion_date']
                })
            return res
        except Exception as e:
            return []

    def _get_recent_activity_context(self, project_id: str) -> str:
        """Fetch recent logs and emails for the project."""
        lines = []
        try:
            conn = self._get_db_conn()
            
            # Get internal ID first
            p_row = conn.execute("SELECT id FROM projects WHERE altimeter_project_id = ?", (project_id,)).fetchone()
            if not p_row:
                return "No recent activity found."
            
            p_uuid = p_row['id']
            
            # 1. Recent Logs
            logs = conn.execute("""
                SELECT log_date, description FROM daily_logs 
                WHERE project_id = ? 
                ORDER BY log_date DESC LIMIT 3
            """, (p_uuid,)).fetchall()
            
            if logs:
                lines.append("Recent Daily Logs:")
                for l in logs:
                    lines.append(f"  - {l['log_date']}: {l['description']}")

            # 2. Linked Emails (from Communications module)
            emails = conn.execute("""
                SELECT date, subject FROM Emails 
                WHERE project_id = ? 
                ORDER BY date DESC LIMIT 3
            """, (project_id,)).fetchall()
            
            if emails:
                lines.append("Recently Linked Emails:")
                for e in emails:
                    lines.append(f"  - {e['date']}: {e['subject']}")

            conn.close()
        except Exception as e:
            pass
            
        return "\n".join(lines) if lines else "No recent activity found."

    def get_project_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetch tasks for a specific project from Altimeter DB."""
        try:
            conn = self._get_db_conn()
            # Assuming 'tasks' table exists
            # We select tasks where project_id matches
            # And we need: id, name, status, updated_at
            query = """
                SELECT id, project_id, name, status, updated_at
                FROM tasks
                WHERE project_id = ? OR project_id = (SELECT id FROM projects WHERE altimeter_project_id = ?)
            """

            rows = conn.execute(query, (project_id, project_id)).fetchall()
            conn.close()

            tasks = []
            for r in rows:
                tasks.append({
                    "id": str(r["id"]),
                    "project_id": r["project_id"],
                    "name": r["name"],
                    "status": r["status"],
                    "updated_at": r["updated_at"]
                })
            return tasks
        except Exception as e:
            # Table might not exist or other error
            return []

class IntelligenceBridge:
    """
    Standardized interface for Altimeter to request AI context from Atlas.
    """
    def fetch_context_from_atlas(self, query: str, context_type: str = "general") -> Dict[str, Any]:
        """
        Retrieves relevant context from Atlas's Knowledge Base (Vector DB)
        to assist Altimeter's decision making.
        """
        try:
            from services.search_service import search_service

            # 1. Search Knowledge Base
            results = search_service.search(query, collection_name="knowledge", n_results=3)

            # 2. Format for Altimeter
            context_data = []
            if results:
                for res in results:
                    context_data.append({
                        "source": res.get("metadata", {}).get("title", "Unknown Source"),
                        "content": res.get("content_snippet", ""),
                        "relevance": res.get("score", 0)
                    })

            return {
                "query": query,
                "context_type": context_type,
                "insights": context_data,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "query": query,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def predict_mission_intel(self, active_phases: List[Dict], weather: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        The Oracle Protocol: Predicts relevant SOPs based on active work and weather.
        """
        from services.search_service import search_service

        intel_results = []
        seen_titles = set()

        # 1. Weather Context Injection
        weather_alert = False
        weather_keywords = []
        if weather:
            # Simple heuristic for bad weather
            condition = weather.get("current", {}).get("condition", "").lower()
            if any(x in condition for x in ["rain", "storm", "snow", "wind", "thunder"]):
                weather_alert = True
                weather_keywords = ["weather", "rain", "storm", "safety", "protection"]

        for phase in active_phases:
            phase_name = phase.get("phase_name", "")
            keywords = [phase_name]

            # 3. Contextual Boosting
            # If outdoor phase + bad weather -> prioritization
            is_outdoor = any(x in phase_name.lower() for x in ["exterior", "foundation", "site", "roof", "ground"])
            if is_outdoor and weather_alert:
                keywords.extend(weather_keywords)
                keywords.insert(0, "Inclement Weather Protocol") # High priority search
            for term in keywords:
                results = search_service.search(term, collection_name="knowledge", n_results=2)
                for res in results:
                    title = res.get("metadata", {}).get("title", "Unknown")
                    if title not in seen_titles:
                        seen_titles.add(title)
                        # Apply Weighting
                        relevance = 1.0
                        if "weather" in term.lower() and weather_alert:
                            relevance = 1.5 # Boost weather docs

                        intel_results.append({
                            "title": title,
                            "type": "SOP",
                            "phase_match": phase_name,
                            "snippet": res.get("content_snippet", ""),
                            "relevance": res.get("score", 0) * relevance,
                            "trigger": "Weather Alert" if (weather_alert and is_outdoor and "weather" in term.lower()) else "Active Phase"
                        })

        # Sort by relevance
        # For this prototype, we'll sort by our custom 'relevance' multiplier first, then by score.
        intel_results.sort(key=lambda x: (x['trigger'] == "Weather Alert", x['relevance']), reverse=True)

        return intel_results[:5] # Top 5

altimeter_service = AltimeterService()
intelligence_bridge = IntelligenceBridge()
