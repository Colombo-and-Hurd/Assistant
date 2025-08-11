
def create_context_completeness_prompt(history, query, context, client_name=None, client_pronouns=None, client_endeavor=None, client_gender=None):
    client_name = client_name or "Not provided"
    client_pronouns = client_pronouns or "Not provided"
    client_endeavor = client_endeavor or "Not provided"
    client_gender = client_gender or "Not provided"

    base_prompt = f"""
You are helping determine whether enough information has been gathered to draft a Letter of Recommendation (LOR) for a client.
You should focus on the user query and the retrieved context to determine the missing fields. If there is a conflict between the user query and the retrieved context, you should prioritize the user query.

## Required Information:
- Client's Full Name
- Client's Pronouns

## Provided Information:
- Client Name: {client_name}
- Client Pronouns: {client_pronouns}
- Client Gender: {client_gender}
- Client Endeavor: {client_endeavor}


IMPORTANT : If the client name and the client pronouns are available then the missing fields should be empty and the follow up question should be empty.
Analyze the context and conversation history step by step to get whether the client name and the client pronouns are available.

## Instructions:
1. Identify which of the required fields are missing (i.e., are "Not provided", None, or empty).
2. Return a JSON object in the following format:

{{
  "missing_fields": ["<name of missing fields>"],
  "follow_up_question": "<politely ask for the missing fields>"
}}

If no fields are missing, return:

{{
  "missing_fields": [],
  "follow_up_question": ""
}}
"""

    if client_name == "Not provided" or client_pronouns == "Not provided":
        base_prompt += f"""

## Additional Context:
Conversation History:
{history}

User's Query:
{query}

Retrieved Context:
{context}
"""

    else:
        base_prompt += f"""

## User's Query:
{query}


Retrieved Context:
{context}
"""

    return base_prompt.strip()