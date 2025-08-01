def generate_entity_extraction_prompt(full_text: str) -> str:
    """Generates the prompt for extracting entities from text."""
    
    prompt = f"""
From the following text, which may be in Spanish or another language, please first translate it to English. Then, from the translated text, judge the missing context.

Context:
---
{full_text}
---

Provide your response as a valid JSON object with two keys: "client_name" and "pronouns".
Example: {{"client_name": "Dr. Jane Doe", "pronouns": "she/her"}}
If you cannot find the information, return null for the corresponding value.
"""
    return prompt.strip() 