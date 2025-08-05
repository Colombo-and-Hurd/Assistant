from pydantic import BaseModel, Field
from typing import List, Optional

class ContextCompleteness(BaseModel):
    """Schema for context completeness check output."""
    missing_fields: List[str] = Field(
        description="List of required information fields that are missing from the context. Return an empty list if all required information is present."
    )
    follow_up_question: Optional[str] = Field(
        description="A follow-up question to ask the user to get the missing information. This should be an empty string if no information is missing."
    )

class ConversationResponse(BaseModel):
    """Schema for conversation agent output."""
    client_name: str = Field(
        default="",
        description="The client's full name if found in the message"
    )
    client_pronouns: str = Field(
        default="",
        description="The client's pronouns if found in the message"
    )
    client_gender: str = Field(
        default="",
        description="The client's gender if found in the message"
    )
    client_endeavor: str = Field(
        default="",
        description="The purpose of the recommendation if found in the message"
    )
    lor_questionnaire: str = Field(
        default="",
        description="The questionnaire responses if found in the message"
    )
    response: str = Field(
        description="The friendly response to send to the user"
    )

class Translation(BaseModel):
    """Schema for translation output."""
    translated_text: str = Field(
        description="The English translation of the provided text. If the text is already in English, return it as is."
    ) 