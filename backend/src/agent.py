import os
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

from openai import BadRequestError
from backend.src.schemas import GraphState
from backend.src.output_schemas import ContextCompleteness, Translation, ConversationResponse
from backend.src.prompts import PromptFactory
from backend.src.prompts.utils import truncate_conversation_history

load_dotenv()

class DocumentGenerationAgent:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
            
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name="gpt-4-turbo-2024-04-09")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large")
        self.vector_store = PineconeVectorStore(
            index_name=self.pinecone_index_name,
            embedding=self.embeddings,
            pinecone_api_key=self.pinecone_api_key
        )
        self.prompt_factory = PromptFactory()

    def process_pdfs(self, file_paths, thread_id: str):
        """
        Loads and chunks PDFs, generates embeddings, and stores them in a
        thread-specific namespace in Pinecone.
        """
        all_docs = []
        for file_path in file_paths:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(documents)
            all_docs.extend(docs)
        
        if all_docs:
            self.vector_store.add_documents(all_docs, namespace=thread_id)
            print(f"Documents have been processed and stored in Pinecone namespace: {thread_id}")
        else:
            print("No documents to process.")

    def retrieve_context(self, state: GraphState):
        """
        Retrieves relevant context from a thread-specific Pinecone namespace.
        It includes a retry mechanism to account for indexing delays.
        """
        print("---RETRIEVING CONTEXT---")
        request = state["request"]
        thread_id = state["thread_id"]
        conversation_history = state.get("conversation_history", [])
        
        history_str = "\n".join(conversation_history)
        retrieval_query = self.prompt_factory.get_prompt("retrieval_query")
        detailed_query = f"User Request: {request}\n\nConversation History:\n{history_str}\n\n{retrieval_query}"
        
        retriever = self.vector_store.as_retriever(search_kwargs={'namespace': thread_id})

        context = []
        for i in range(3):
            context = retriever.invoke(detailed_query)
            if context:
                print(f"Context retrieved successfully on attempt {i+1}.")
                break
            print(f"Attempt {i+1}: Context is empty, retrying in 1 second...")
            time.sleep(1 + i * 2)

        print("retrieved context: ", context)
        return {"retrieved_context": context}

    def translate_context_to_english(self, state: GraphState):
        """Translates the retrieved context to English using an LLM."""
        print("---TRANSLATING CONTEXT TO ENGLISH---")
        context = state.get("retrieved_context", [])
        
        if not context:
            print("No context to translate")
            return {"translated_context": ""}

        context_text = " ".join([doc.page_content for doc in context])
        
        prompt = self.prompt_factory.get_prompt("translation", context_text)
        structured_llm = self.llm.with_structured_output(Translation)
        response = structured_llm.invoke(prompt)
        
        print("Translated context: ", response.translated_text)
        return {"translated_context": response.translated_text}

    def context_completeness_check(self, state: GraphState):
        """
        Checks if the context is complete and generates a follow-up question if needed.
        """
        print("---CHECKING CONTEXT COMPLETENESS---")
        request = state["request"]
        conversation_history = state.get("conversation_history", [])
        
        if not state.get("retrieved_context"):
            context = "\n".join(conversation_history)
        else:
            context = state["translated_context"]

        history_str = "\n".join(conversation_history)
        
        client_name = state.get("client_name", "Not provided")
        client_pronouns = state.get("client_pronouns", "Not provided")
        client_endeavor = state.get("client_endeavor", "Not provided")
        client_gender = state.get("client_gender", "Not provided")
    
        
        prompt = self.prompt_factory.get_prompt(
            "context_completeness",
            history=history_str,
            query=request,
            context=context,
            client_name=client_name,
            client_pronouns=client_pronouns,
            client_gender=client_gender,
            client_endeavor=client_endeavor
        )
        
        print("---CURRENT STATE VALUES---")
        print(f"Client Name: {state.get('client_name', '')}")
        print(f"Client Pronouns: {state.get('client_pronouns', '')}")
        print(f"Client Endeavor: {state.get('client_endeavor', '')}")
        print(f"Client Gender: {state.get('client_gender', '')}")
        
        structured_llm = self.llm.with_structured_output(ContextCompleteness)
        response = structured_llm.invoke(prompt)
        
        print("---CONTEXT COMPLETENESS RESPONSE---", response)
        
        if response.missing_fields:
            if not response.follow_up_question:
                print("---FALLBACK IN CASE THE LLM FAILS TO GENERATE A QUESTION---")
                missing_fields_str = ", ".join(response.missing_fields)
                response.follow_up_question = f"It looks like I'm missing some information. Could you please provide the following details: {missing_fields_str}?"
            
            state["follow_up_question"] = response.follow_up_question
            state["missing_fields"] = response.missing_fields
            return state
        else:
            state["follow_up_question"] = ""
            state["missing_fields"] = []
            if not state.get("retrieved_context"):
                state["translated_context"] = context
            return state

    def generate_document(self, state: GraphState):
        """
        Generates a document by building a detailed prompt and invoking the LLM.
        """
        print("---GENERATING DOCUMENT---")
        context = state["translated_context"]
        conversation_history = state.get("conversation_history", [])

        history_str = "\n".join(conversation_history)
        full_context = f"Retrieved Context: {context}\n\nConversation History:\n{history_str}"
        
        lor_system_prompt = self.prompt_factory.get_prompt("lor_system", full_context)

        print("---CALLING LLM WITH DETAILED LOR PROMPT---")
        generated_doc = self.llm.invoke(lor_system_prompt)
        print("generated_doc: ", generated_doc)
        state["generated_document"] = generated_doc.content
        return state
        
    def request_user_info(self, state: GraphState):
        """
        If information is missing, this node is called.
        It signals that the graph should pause to wait for user input.
        """
        print("---REQUESTING USER INFO---")
        return {}

    def context_gatherer_agent(self, state: GraphState):
        """
        Handles the conversational flow, responding to user queries and maintaining context.
        Uses LLM to extract information and generate appropriate responses.
        """
        print("---CONTEXT GATHERER AGENT---")
        state["missing_fields"] = []
        request = state["request"]
        conversation_history = state.get("conversation_history", [])
        
        try:
            history_str = truncate_conversation_history(conversation_history)
            conversational_prompt = self.prompt_factory.get_prompt("conversation", request, conversation_history=history_str)
            
            structured_llm = self.llm.with_structured_output(ConversationResponse)
            response = structured_llm.invoke(conversational_prompt)
            
            print("---EXTRACTED INFORMATION---")
            
            # Update state with any non-empty values
            for field in ["client_name", "client_pronouns", "client_endeavor", "lor_questionnaire"]:
                value = getattr(response, field, "")
                if value:  # Only update if value is non-empty
                    state[field] = value
                    print(f"Updated {field}: {value}")
            
            # Store the response
            state["conversational_response"] = response.response
            print("conversational_response:", response.response)
            
            # Print final state for verification
            print("\n---FINAL STATE AFTER UPDATES---")
            print(f"Client Name: {state.get('client_name', '')}")
            print(f"Client Pronouns: {state.get('client_pronouns', '')}")
            print(f"Client Endeavor: {state.get('client_endeavor', '')}")
            print(f"LOR Questionnaire: {state.get('lor_questionnaire', '')}")
            
            return state
            
        except BadRequestError as e:
            if "context_length_exceeded" in str(e):
                print("Context length exceeded, retrying with minimal history...")
                history_str = truncate_conversation_history(conversation_history, max_messages=3)
                conversational_prompt = self.prompt_factory.get_prompt("conversation", request, conversation_history=history_str)
                
                structured_llm = self.llm.with_structured_output(ConversationResponse)
                response = structured_llm.invoke(conversational_prompt)
                
                for key, value in response.extracted_info.items():
                    if value is not None:
                        state[key] = value
                        print(f"Updated {key}: {value}")
                
                state["conversational_response"] = response.response
                print("conversational_response: ", response.response)
                return state
            raise