def generate_translation_prompt(text_to_translate: str) -> str:
    """Generates the prompt for translating text to English."""
    
    prompt = f"""
Please translate the following text to English.
If the text is already in English, simply return the original text.

---
{text_to_translate}
---
"""
    return prompt.strip() 