from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import List, Optional
import os
import uuid

from .graph import create_graph
from .schemas import GenerationResponse

app = FastAPI()

# using in memory thread id management for now for the quick MVP - Deepak
graphs = {}
agents = {}

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/generate", response_model=GenerationResponse)
async def generate(
    prompt: str = Form(...),
    files: Optional[List[UploadFile]] = File(None),
    thread_id: Optional[str] = Form(None),
):
    """
    Single endpoint to handle document generation. It supports PDF uploads
    on the initial call and manages an interactive conversation with the
    LangGraph agent.
    """
    if thread_id and thread_id not in graphs:
        raise HTTPException(
            status_code=404, detail="Thread ID not found. Please start a new conversation."
        )

    config = {}
    app_instance = None

    if not thread_id:
        thread_id = str(uuid.uuid4())
        app_instance, agent_instance = create_graph()
        graphs[thread_id] = app_instance
        agents[thread_id] = agent_instance
        config = {"configurable": {"thread_id": thread_id}}

        if files:
            file_paths = []
            for file in files:
                file_path = os.path.join(UPLOAD_DIR, f"{thread_id}_{file.filename}")
                with open(file_path, "wb") as buffer:
                    buffer.write(await file.read())
                file_paths.append(file_path)
            
            agent_instance.process_pdfs(file_paths, thread_id)

        required_info = [
            "the full name of the client",
            "the client's pronouns",
            "details of the recommender's expertise and credentials",
            "the professional relationship between the recommender and the client",
            "a clear description of the client's proposed work/project in the U.S.",
            "at least two specific examples of the client's key achievements and contributions"
        ]
        
        initial_state = {
            "request": prompt,
            "required_info": required_info,
            "thread_id": thread_id,
        }
        
        app_instance.invoke(initial_state, config)

    else:
        app_instance = graphs[thread_id]
        config = {"configurable": {"thread_id": thread_id}}
        app_instance.update_state(config, {"user_provided_info": prompt})
        app_instance.invoke(None, config)

    current_state = app_instance.get_state(config)
    
    if current_state.next:
        missing_fields = current_state.values.get('missing_fields', [])
        response_prompt = f"To generate a high-quality LOR, I need more information. Please provide details on: {', '.join(missing_fields)}"
        return GenerationResponse(
            thread_id=thread_id,
            response=response_prompt,
            status="requires_input"
        )
    else:
        final_doc = current_state.values.get('generated_document')
        return GenerationResponse(
            thread_id=thread_id,
            response="Document generation is complete.",
            status="complete",
            document=final_doc
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 