def get_conversation_prompt(request: str, conversation_history: str) -> str:
    """
    Generates the prompt for the context gatherer agent.
    
    Args:
        request: The user's current request
        conversation_history: String containing the conversation history
    
    Returns:
        str: The formatted conversation prompt
    """
    return (
        "You are an expert at gathering information for a Letter of Recommendation (LOR). "
        "Your task is to:\n"
        "1. Extract any provided information from the user's message\n"
        "2. Ask for missing information in a friendly way\n\n"
        "Required Information:\n"
        "- client_name: The full name of the person receiving the recommendation\n"
        "- client_pronouns: Their preferred pronouns (e.g., he/him, she/her)\n"
        "- client_endeavor: What the recommendation is for (job, program, etc.)\n"
        "- lor_questionnaire: Their completed questionnaire responses\n\n"
        "Instructions:\n"
        "1. Analyze the user's message for any of the required information\n"
        "2. Return the extracted information in the specified format\n"
        "3. Generate a friendly response asking for any missing information\n"
        "4. DO NOT draft the letter itself\n\n"
        "IMPORTANT: You must return a JSON object with these fields:\n"
        "{\n"
        '  "client_name": "",\n'
        '  "client_pronouns": "",\n'
        '  "client_endeavor": "",\n'
        '  "client_gender": "",\n'
        '  "lor_questionnaire": "",\n'
        '  "response": "Hello! I\'d be happy to help you with your letter of recommendation. Could you please provide the name of the person this recommendation is for?"\n'
        "}\n\n"
        "Rules:\n"
        "1. Extract any information found in the message\n"
        "2. Use empty strings for information not found\n"
        "3. Make the response friendly and ask for missing information\n\n"
        f"User Request: {request}\n"
        "--------------------------------\n"
        f"Conversation History: {conversation_history}"
    )
