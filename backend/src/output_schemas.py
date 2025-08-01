from pydantic import BaseModel, Field
from typing import List, Optional

class ContextCompleteness(BaseModel):
    """Schema for context completeness check output."""
    missing_fields: List[str] = Field(
        description="List of required information fields that are missing from the context. Return an empty list if all required information is present."
    )
    follow_up_question: str = Field(
        description="A follow-up question to ask the user to get the missing information. This should be an empty string if no information is missing."
    )

class EntityExtraction(BaseModel):
    """Schema for entity extraction output."""
    client_name: Optional[str] = Field(
        description="The full name of the client/person this document is about. Return null if not found."
    )
    pronouns: Optional[str] = Field(
        description="The pronouns used for the client (e.g., 'she/her', 'he/him', 'they/them'). Return null if not found."
    )

class Translation(BaseModel):
    """Schema for translation output."""
    translated_text: str = Field(
        description="The English translation of the provided text. If the text is already in English, return it as is."
    ) 