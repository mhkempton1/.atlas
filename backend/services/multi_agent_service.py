from typing import Dict, Any, Optional
from services.ai_service import ai_service

class BaseAgent:
    def __init__(self, name: str, role_prompt: str):
        self.name = name
        self.role_prompt = role_prompt

    async def process(self, query: str, context: str = "") -> str:
        full_prompt = f"{self.role_prompt}\n\nUSER QUERY: {query}\n\nCONTEXT:\n{context}"
        return await ai_service.generate_content(full_prompt)

class LibrarianAgent(BaseAgent):
    def __init__(self):
        super().__init__("Librarian",
            "You are the Librarian. You manage Documents, SOPs, and Safety Policies. "
            "If the user asks for a document, search the Knowledge Base."
        )

class ForemanAgent(BaseAgent):
    def __init__(self):
        super().__init__("Foreman",
            "You are the Foreman. You manage Tasks, Schedules, and Logistics. "
            "You focus on execution, tools, and daily briefings."
        )

class AgentRouter:
    def __init__(self):
        self.librarian = LibrarianAgent()
        self.foreman = ForemanAgent()

    async def route_and_execute(self, query: str, user_strata: int) -> Dict[str, Any]:
        """
        Analyzes intent and dispatches to the right agent.
        """
        # 1. Intent Analysis
        intent_prompt = f"""
        Classify the intent of this query into one of: [DOCUMENT_SEARCH, TASK_MANAGEMENT, GENERAL_CHAT].
        Query: {query}
        Output just the category.
        """
        intent = await ai_service.generate_content(intent_prompt)
        intent = intent.strip().upper() if intent else "GENERAL_CHAT"

        print(f"AgentRouter: Routing '{query}' -> {intent}")

        # 2. Dispatch
        if "DOCUMENT" in intent:
            response = await self.librarian.process(query)
            return {"reply": response, "agent": "Librarian"}
        elif "TASK" in intent or "SCHEDULE" in intent:
            response = await self.foreman.process(query)
            return {"reply": response, "agent": "Foreman"}
        else:
            # Fallback to general chat (Jules)
            return {"reply": None, "agent": "Jules"}

agent_router = AgentRouter()
