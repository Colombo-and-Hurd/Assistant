import os
import time
import uuid
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores.azuresearch import AzureSearch
from azure.search.documents.indexes.models import (
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchIndex,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.search.documents.models import VectorizedQuery


from dotenv import load_dotenv

from openai import BadRequestError
from backend.src.schemas import GraphState
from backend.src.output_schemas import ContextCompleteness, ConversationResponse
from backend.src.prompts import PromptFactory
from backend.src.prompts.utils import truncate_conversation_history

load_dotenv()

class DocumentGenerationAgent:
    def __init__(self):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
            
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key, model_name="gpt-4-turbo-2024-04-09")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large")

        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True,
                retrievable=True,
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchableField(
                name="metadata",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=3072,
                vector_search_profile_name="my-vector-search-profile",
            ),
            SimpleField(
                name="thread_id",
                type=SearchFieldDataType.String,
                filterable=True,
                searchable=True,
            ),
        ]
        
        vector_search = VectorSearch(
            profiles=[VectorSearchProfile(name="my-vector-search-profile", algorithm_configuration_name="my-algorithms-config")],
            algorithms=[HnswAlgorithmConfiguration(name="my-algorithms-config")],
        )
        
        index = SearchIndex(name=os.getenv("AZURE_SEARCH_INDEX"), fields=fields, vector_search=vector_search)
        
        from azure.search.documents.indexes import SearchIndexClient
        from azure.core.credentials import AzureKeyCredential
        
        index_client = SearchIndexClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
        )
        if os.getenv("AZURE_SEARCH_INDEX") not in index_client.list_index_names():
            index_client.create_index(index)
            print(f"Index '{os.getenv('AZURE_SEARCH_INDEX')}' created.")
        else:
            print(f"Index '{os.getenv('AZURE_SEARCH_INDEX')}' already exists.")

        self.vector_store = AzureSearch(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX"),
            embedding_function=self.embeddings.embed_query,
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
            
            for doc in docs:
                doc.metadata = {"thread_id": thread_id}

            all_docs.extend(docs)
        
        if all_docs:
            batch_size = 10
            batches = [all_docs[i:i + batch_size] for i in range(0, len(all_docs), batch_size)]
            
            for batch in batches:
                texts = [doc.page_content for doc in batch]
                embeddings = self.embeddings.embed_documents(texts)
                
                documents_to_upload = []
                for i, doc in enumerate(batch):
                    documents_to_upload.append(
                        {
                            "id": str(uuid.uuid4()),
                            "content": texts[i],
                            "content_vector": embeddings[i],
                            "thread_id": doc.metadata["thread_id"],
                            "metadata": json.dumps(doc.metadata),
                        }
                    )
                
                self.vector_store.client.upload_documents(documents=documents_to_upload)
                print(f"Processed batch of {len(batch)} documents.")

            print(f"Documents have been processed and stored in Azure AI Search for thread: {thread_id}")
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
        
        vector_query = VectorizedQuery(
            vector=self.embeddings.embed_query(detailed_query),
            k_nearest_neighbors=5,
            fields="content_vector",
        )

        context = []
        for i in range(3):
            results = self.vector_store.client.search(
                search_text=detailed_query,
                vector_queries=[vector_query],
                filter=f"thread_id eq '{thread_id}'",
                select=["content", "metadata"],
            )
            context = []
            for result in results:
                metadata = json.loads(result.get("metadata", "{}"))
                context.append({
                    "page_content": result["content"],
                    "metadata": metadata
                })
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

        context_text = " ".join([doc["page_content"] for doc in context])
        
        prompt = self.prompt_factory.get_prompt("translation", context_text)
        
        response = self.llm.invoke(prompt)
        print("Raw response: ", response.content)
        
        try:
            import json
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

    def context_completeness_check(self, state: GraphState):
        """
        Checks if the context is complete and generates a follow-up question if needed.
        """
        print("---CHECKING CONTEXT COMPLETENESS---")
        state["missing_fields"] = []
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
            
            for field in ["client_name", "client_pronouns", "client_endeavor", "lor_questionnaire"]:
                value = getattr(response, field, "")
                if value:  # Only update if value is non-empty
                    state[field] = value
                    print(f"Updated {field}: {value}")
            
            state["conversational_response"] = response.response
            print("conversational_response:", response.response)
            
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