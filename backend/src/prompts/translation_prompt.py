def generate_translation_prompt(text_to_translate: str) -> str:
    """Generates the prompt for translating text to English."""
    
    prompt = f"""
You are a translation assistant that MUST return responses in a specific JSON format.

TASK:
1. Translate the following text to English
2. If the text is already in English, return it unchanged
3. Return ONLY a JSON object with this exact structure: {{"translated_text": "your translation here"}}

RULES:
- Your entire response must be valid JSON
- Include ONLY the JSON object, no other text
- Do not add comments, explanations, or any other content
- Ensure all quotes are properly escaped in the translation

INPUT TEXT:
---
{text_to_translate}
---

RESPONSE FORMAT:
{{"translated_text": "your translation here"}}
"""
    return prompt.strip() 