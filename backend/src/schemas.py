from pydantic import BaseModel
from typing import List, Any, Optional, TypedDict
from langchain_core.documents import Document

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        request: The user's request for document generation.
        retrieved_context: The context retrieved from the vector store.
        required_info: A list of required information fields for the document.
        missing_fields: A list of fields that are missing from the context.
        user_provided_info: Information provided by the user to fill in the gaps.
        generated_document: The final generated document.
        client_name: Optional name of the person for whom the document is generated.
        pronouns: Optional pronouns for the client.
        thread_id: The unique identifier for the conversation thread.
        conversation_history: A list of messages in the conversation.
    """
    request: str
    thread_id: str
    retrieved_context: List[Document]
    translated_context: str
    required_info: List[str]
    user_provided_info: str
    missing_fields: List[str]
    follow_up_question: str
    generated_document: str
    conversation_history: List[str]

class GenerationResponse(BaseModel):
    thread_id: str
    response: str
    status: str
    document: Optional[str] = None 