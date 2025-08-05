from typing import Optional

def get_routing_prompt(request: str, conversation_history: Optional[str] = None) -> str:
    """
    Generates the prompt for routing user requests between conversation and document generation.
    
    Args:
        request: The user's current request
        conversation_history: Optional string containing the conversation history
    
    Returns:
        str: The formatted routing prompt
    """
    return (
        "You are an expert legal-writing assistant specializing in drafting professional Letters of Recommendation (LORs) for EB-2 National Interest Waiver (NIW) immigration petitions, collaborating with Colombo & Hurd. Your core task is to guide users through a structured, compliant workflow for LOR production."
        "Determine the user’s intent: document generation, information request, or general question"
        "If the we have the enough context to generate the documentation then we should move to the document generation process."
        "If the user is asking a general question, respond with 'conversational_agent'."
        "The document generation process is about creating a letter of recommendation."
        "NOTE: Do consider the conversation history to determine the user's intent."
        


        f"User Request: {request}\n"
        "-------------------------------------------------"
        f"Conversation History: {conversation_history if conversation_history else 'No previous conversation'}"
    )