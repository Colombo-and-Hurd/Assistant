from .routing_prompt import get_routing_prompt
from .conversation_prompt import get_conversation_prompt
from .context_completeness_prompt import create_context_completeness_prompt
from .translation_prompt import generate_translation_prompt
from .lorSystemPrompt import RETRIEVAL_QUERY_TEMPLATE, generate_LOR_prompt
from .master_router_prompt import master_router_prompt

class PromptFactory:
    def __init__(self):
        self.prompts = {
            "routing": get_routing_prompt,
            "conversation": get_conversation_prompt,
            "context_completeness": create_context_completeness_prompt,
            "translation": generate_translation_prompt,
            "lor_system": generate_LOR_prompt,
            "retrieval_query": lambda: RETRIEVAL_QUERY_TEMPLATE,
            "master_router": lambda: master_router_prompt,
        }

    def get_prompt(self, prompt_name: str, *args, **kwargs) -> str:
        """
        Get a prompt by name and format it with the provided arguments.
        
        Args:
            prompt_name: The name of the prompt to retrieve
            *args: Positional arguments to pass to the prompt function
            **kwargs: Keyword arguments to pass to the prompt function
        
        Returns:
            str: The formatted prompt
            
        Raises:
            ValueError: If the prompt name is not found in the factory
        """
        prompt_func = self.prompts.get(prompt_name)
        if prompt_func:
            if kwargs or args:
                return prompt_func(*args, **kwargs)
            return prompt_func()
        else:
            raise ValueError(f"Prompt '{prompt_name}' not found in the factory.")
