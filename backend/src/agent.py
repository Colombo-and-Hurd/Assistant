import os
import json
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv

from backend.src.schemas import GraphState
from backend.src.output_schemas import ContextCompleteness, Translation
from backend.src.prompts.lorSystemPrompt import RETRIEVAL_QUERY_TEMPLATE, generate_LOR_prompt
from backend.src.prompts.context_completeness_prompt import context_completeness_prompt
from backend.src.prompts.translation_prompt import generate_translation_prompt

load_dotenv()

class DocumentGenerationAgent:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
            
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name="gpt-4o")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large")
        self.vector_store = PineconeVectorStore(
            index_name=self.pinecone_index_name,
            embedding=self.embeddings,
            pinecone_api_key=self.pinecone_api_key
        )

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
        detailed_query = f"User Request: {request}\n\nConversation History:\n{history_str}\n\n{RETRIEVAL_QUERY_TEMPLATE}"
        
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
        
        prompt = generate_translation_prompt(context_text)
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
        context = state["translated_context"]
        conversation_history = state.get("conversation_history", [])
        
        history_str = "\n".join(conversation_history)
        
        prompt = context_completeness_prompt.format(
            history=history_str, query=request, context=context
        )
        
        structured_llm = self.llm.with_structured_output(ContextCompleteness)
        response = structured_llm.invoke(prompt)
        
        print("---CONTEXT COMPLETENESS RESPONSE---")
        print(response)
        
        if response.missing_fields:
            state["follow_up_question"] = response.follow_up_question
            state["missing_fields"] = response.missing_fields
            return state
        else:
            state["follow_up_question"] = ""
            state["missing_fields"] = ""
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
        
        lor_system_prompt = generate_LOR_prompt(full_context)

        print("---CALLING LLM WITH DETAILED LOR PROMPT---")
        generated_doc = self.llm.invoke(lor_system_prompt)
        print("generated_doc: ", generated_doc)
        return {"generated_document": generated_doc.content}
        
    def request_user_info(self, state: GraphState):
        """
        If information is missing, this node is called.
        It signals that the graph should pause to wait for user input.
        """
        print("---REQUESTING USER INFO---")
        return {}