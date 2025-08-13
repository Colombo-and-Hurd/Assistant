import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from backend.src.schemas import GraphState
from backend.src.prompts import PromptFactory

load_dotenv()

class OrchestratorAgent:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        
        self.llm = ChatOpenAI(openai_api_key=openai_api_key, model_name="gpt-5-2025-08-07")
        self.prompt_factory = PromptFactory()

    def master_router(self, state: GraphState):
        """
        The master router for the graph.
        """
        print("---MASTER ROUTER---")
        conversation_history = state.get("conversation_history", [])
        request = state["request"]
        files = state.get("files", [])

        history_str = "\n".join(conversation_history)

        prompt = self.prompt_factory.get_prompt("master_router").format(
            history=history_str, request=request, files=files
        )
        response = self.llm.invoke(prompt)
        print("Orchestrator Response: ", response.content)
        if "retrieve_context" in response.content.lower():
            print("---ROUTING TO RETRIEVE CONTEXT---")
            return "retrieve_context"
        elif "context_completeness_check" in response.content.lower():
            print("---ROUTING TO CONTEXT COMPLETENESS CHECK---")
            return "context_completeness_check"
        else:
            print("---ROUTING TO CONTEXT GATHERER AGENT---")
            return "context_gatherer_agent"
