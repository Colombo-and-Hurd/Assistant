from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.src.schemas import GraphState
from backend.src.agent import DocumentGenerationAgent

def decide_next_node(state: GraphState) -> str:
    """
    Determines the next node to visit based on context completeness.
    """
    if not state["missing_fields"]:
        print("---CONTEXT IS COMPLETE---")
        return "generate_document"
    else:
        print("---CONTEXT IS INCOMPLETE, PAUSING FOR USER INPUT---")
        return "request_user_info"

def create_graph():
    """
    Creates and compiles the LangGraph agent.
    """
    agent = DocumentGenerationAgent()
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve_context", agent.retrieve_context)
    workflow.add_node("translate_context_to_english", agent.translate_context_to_english)
    workflow.add_node("generate_document", agent.generate_document)
    workflow.add_node("request_user_info", agent.request_user_info)

    workflow.add_node("context_completeness_check", agent.context_completeness_check)

    workflow.set_entry_point("retrieve_context")

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

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory, interrupt_before=["request_user_info"])
    
    return app, agent