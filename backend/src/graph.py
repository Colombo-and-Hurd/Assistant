from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.src.schemas import GraphState
from backend.src.agent import DocumentGenerationAgent
from backend.src.orchestrator import OrchestratorAgent
from backend.src.nodes.translate_context_node import TranslateContextNode

def decide_next_node(state: GraphState) -> str:
    """
    Determines the next node to visit based on context completeness.
    """
    if not state["missing_fields"]:
        print("---CONTEXT IS COMPLETE---")
        return "generate_document"
    else:
        print("---CONTEXT IS INCOMPLETE, PAUSING FOR USER INPUT---")
        state["missing_fields"] = []
        return "request_user_info"

def create_graph():
    """
    Creates and compiles the LangGraph agent.
    """
    agent = DocumentGenerationAgent()
    translate_node = TranslateContextNode()
    orchestrator = OrchestratorAgent()
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve_context", agent.retrieve_context)
    workflow.add_node("translate_context_to_english", translate_node.execute)
    workflow.add_node("generate_document", agent.generate_document)
    workflow.add_node("request_user_info", agent.request_user_info)
    workflow.add_node("context_completeness_check", agent.context_completeness_check)
    workflow.add_node("context_gatherer_agent", agent.context_gatherer_agent)
    workflow.add_node("master_router", orchestrator.master_router)

    workflow.set_conditional_entry_point(
        orchestrator.master_router,
        {
            "retrieve_context": "retrieve_context",
            "context_gatherer_agent": "context_gatherer_agent",
            "context_completeness_check": "context_completeness_check",
        },
    )

    workflow.add_edge("retrieve_context", "translate_context_to_english")
    workflow.add_edge("translate_context_to_english", "context_completeness_check")
    workflow.add_conditional_edges(
        "context_completeness_check",
        decide_next_node,
        {
            "generate_document": "generate_document",
            "request_user_info": "request_user_info",
        },
    )
    workflow.add_edge("generate_document", END)
    workflow.add_edge("context_gatherer_agent", END)
    workflow.add_edge("request_user_info","context_completeness_check")

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["request_user_info"])
    
    return app, agent
