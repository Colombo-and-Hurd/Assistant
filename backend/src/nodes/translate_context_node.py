import os
import json

from langchain_openai import ChatOpenAI

from backend.src.schemas import GraphState
from backend.src.prompts import PromptFactory


class TranslateContextNode:
    """Node responsible for translating retrieved context into English.

    Uses a faster OpenAI chat model specifically for translation to reduce latency
    without impacting the rest of the pipeline's model choices.
    """

    def __init__(self, model_name: str | None = None):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")

        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=model_name or os.getenv("TRANSLATION_MODEL_NAME", "gpt-4o-mini")
        )

        self.prompt_factory = PromptFactory()

    def execute(self, state: GraphState):
        """Translate accumulated context into English and persist on state.

        Args:
            state: The current graph state

        Returns:
            Updated state with `translated_context` set.
        """
        print("---TRANSLATING CONTEXT TO ENGLISH ---")
        context = state.get("retrieved_context", [])

        if not context:
            print("No context to translate")
            state["translated_context"] = ""
            return state

        context_text = " ".join([doc["page_content"] for doc in context])
        prompt = self.prompt_factory.get_prompt("translation", context_text)

        response = self.llm.invoke(prompt)
        print("Raw response (translation): ", response.content)

        try:
            parsed = json.loads(response.content)
            if isinstance(parsed, dict) and "translated_text" in parsed:
                translated_text = parsed["translated_text"]
            else:
                translated_text = response.content
        except json.JSONDecodeError:
            print("JSON parsing failed, using raw response")
            translated_text = response.content

        state["translated_context"] = translated_text
        return state


