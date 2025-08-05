from typing import List

def truncate_conversation_history(history: List[str], max_messages: int = 10) -> str:
    """
    Truncates the conversation history to keep only the most recent messages.
    
    Args:
        history: List of conversation messages
        max_messages: Maximum number of messages to keep
        
    Returns:
        str: Truncated conversation history
    """
    if len(history) > max_messages:
        history = history[-max_messages:]
    return "\n".join(history)