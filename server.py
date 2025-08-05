import pyautogui
import time
import random

print("Starting in 5 seconds...")
time.sleep(5)

code_snippet = """
# LangGraph Document Generation Agent

## Overview

This document outlines the detailed features, workflows, and basic architecture for developing a LangGraph agent designed to:

1. Accept multiple PDF uploads.
2. Chunk PDFs, generate embeddings, and store them in Pinecone DB.
3. Generate user-requested documents such as Letters of Recommendation (LOR).
4. Interactively query the user if required information is missing.
5. Provide a minimal frontend interface for user interactions.

---

## Feature Breakdown

### 1. PDF Upload & Processing

#### Features:

* **Multiple File Uploads:** Users can upload multiple PDF documents simultaneously.
* **Chunking:** PDFs are automatically chunked into manageable text segments using libraries like PyMuPDF or LangChain's built-in loaders.
* **Embeddings Generation:** Each chunk is converted into embeddings using OpenAI's embedding models or similar.
* **Embedding Storage:** Embeddings are stored in Pinecone DB with metadata (document name, upload date, chunk index).

### Workflow:

* User uploads PDFs via the frontend.
* PDFs are processed in the backend, and chunks are generated.
* Chunks converted to embeddings and saved in Pinecone DB.

---

### 2. Pinecone DB Integration

#### Features:

* **Metadata Support:** Embeddings stored with useful metadata for easy retrieval.
* **Efficient Retrieval:** Quick and accurate semantic search capabilities.

### Workflow:

* Embeddings are stored along with relevant metadata.
* Pinecone DB queried by the agent based on user's requests.

---

### 3. Document Generation & Context Utilization

#### Features:

* **Customizable Templates:** Supports templates for documents like Letters of Recommendation, reports, etc.
* **Contextual Information Retrieval:** Agent retrieves relevant context from Pinecone DB.
* **Dynamic Filling:** Templates dynamically filled based on retrieved context.

### Workflow:

* User requests document generation (e.g., LOR).
* Agent queries Pinecone DB to fetch the required context.
* Context injected into the specified template.
* Document generated and returned to the user.

---

### 4. Interactive User Queries

#### Features:

* **Missing Information Detection:** Agent identifies if context retrieved is insufficient.
* **Interactive Follow-up:** Agent asks user for additional information when required.
* **Seamless User Interaction:** Minimal frontend prompts user clearly and efficiently.

### Workflow:

* Agent attempts to fill the template with available context.
* If insufficient context detected, agent prompts user via frontend.
* User provides additional required details.
* Agent resumes document generation and delivers final document.

---

### 5. Minimal Frontend Interface

#### Features:

* **File Upload Component:** Allows uploading multiple PDFs.
* **Request Input Form:** Simple input field to specify required documents (e.g., "Generate a Letter of Recommendation for client ABC.").
* **Interactive Prompt Component:** Displays questions from agent if extra details are required.
* **Download/View Component:** Allows users to view or download generated documents.

### Minimal Components:

* **Frontend Framework:** NextJS.
* **Components:**

  * File uploader.
  * Text input area for document requests.
  * Interactive prompt display.
  * Download button/link for generated documents.

---

## Technical Stack Recommendation

* **Backend:**

  * LangGraph
  * LangChain for PDF loading and chunking
  * OpenAI embeddings (text-embedding-ada-002)
  * Pinecone DB for embedding storage

* **Frontend:**

  * NextJS
  * Store the conversation history in the localstorage and share the new appended user prompt each time with the backend
  * Axios or fetch API for backend communication

---

## Basic Architecture Diagram

```
User
 │
 ├── Frontend (NextJS)
 │     │
 │     ├── PDF Upload
 │     ├── Document Request
 │     └── Interactive Prompt/Display
 │
 └── Backend (LangGraph)
       │
       ├── PDF Chunking & Embedding Generation
       ├── Embeddings Storage (Pinecone)
       ├── Context Retrieval & Template Filling
       └── Interactive Query Handling
```

---

## Sample Agent Workflow

1. **User uploads PDFs:** Backend chunks, generates embeddings, and stores them.
2. **User requests LOR:** Backend fetches context from Pinecone.
3. **Check completeness:** If complete, generate and return the document. If incomplete, ask the user for required details.
4. **User provides additional details:** Generate and deliver the final document.

---

This feature document serves as the foundational guideline for building a scalable, interactive LangGraph-based document generation system.



the backend graph will look something like this : 
[ User ]
   │
   ▼
[ Frontend (NextJS) ]
   │
   ├─── PDF Upload ────────────┐
   │                           │
   ├─── Document Request ────┐ │
   │                         │ │
   └─── Interactive Prompt ◄─┤ │
         (if required)       │ │
                             │ │
                             ▼ ▼
                 [ Backend (LangGraph Agent) ]
                             │
                             ▼
         ┌─────────────────────────────────────────┐
         │                                         │
         ▼                                         ▼
[PDF Chunking & Embedding] ──────► [Embeddings Storage (Pinecone DB)]
                                                   │
                                                   ▼
                                   [Context Retrieval (Pinecone DB)]
                                                   │
                                                   ▼
                              ┌─────────────────────────────┐
                              │ Check Context Completeness  │
                              └─────────────┬───────────────┘
                                            │
                        ┌───────────────────┴────────────────────┐
                        ▼                                        ▼
       [Sufficient Context Available]       [Insufficient Context Detected]
                 │                                      │
                 ▼                                      ▼
     [Document Generation]                   [Interactive User Prompt]
                 │                                      │
                 ▼                                      ▼
   [Document Delivered to User]         [User Provides Additional Information]
                                                        │
                                                        ▼
                                             [Context Update & Retry]
                                                        │
                                                        ▼
                                            [Document Generation & Delivery]

                                            




# Welcome to Chainlit! 🚀🤖

Hi there, Developer! 👋 We're excited to have you on board. Chainlit is a powerful tool designed to help you prototype, debug and share applications built on top of LLMs.

## Useful Links 🔗

- **Documentation:** Get started with our comprehensive [Chainlit Documentation](https://docs.chainlit.io) 📚
- **Discord Community:** Join our friendly [Chainlit Discord](https://discord.gg/k73SQ3FyUh) to ask questions, share your projects, and connect with other developers! 💬

We can't wait to see what you create with Chainlit! Happy coding! 💻😊

## Welcome screen

To modify the welcome screen, edit the `chainlit.md` file at the root of your project. If you do not want a welcome screen, just leave this file empty.

"""

# Simulate typing
pyautogui.write(code_snippet, interval=1)

# Random mouse movement for activity tracking
for _ in range(10):
    x, y = random.randint(100, 500), random.randint(100, 500)
    pyautogui.moveTo(x, y, duration=0.05)
    time.sleep(1)

print("Task completed!")
