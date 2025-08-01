import sys
import os
import uuid
from typing import List

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl
from langgraph.graph import END

from backend.src.graph import create_graph
from backend.src.agent import DocumentGenerationAgent

UPLOAD_DIR = os.path.join(project_root, "backend", "uploaded_pdfs")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@cl.on_chat_start
async def on_chat_start():
    try:
        app, agent = create_graph()
        cl.user_session.set("graph", app)
        cl.user_session.set("agent", agent)
        cl.user_session.set("conversation_history", [])
        
        thread_id = str(uuid.uuid4())
        cl.user_session.set("thread_id", thread_id)

        files = None
        while files is None:
            files = await cl.AskFileMessage(
                content="Please upload your PDF documents to begin!",
                accept=["application/pdf"],
                max_size_mb=100,
                max_files=10,
                timeout=300,
            ).send()
        
        file_paths = []
        for file_info in files:
            file_path = os.path.join(UPLOAD_DIR, f"{thread_id}_{file_info.name}")
            with open(file_info.path, "rb") as f_in, open(file_path, "wb") as f_out:
                f_out.write(f_in.read())
            file_paths.append(file_path)

        agent.process_pdfs(file_paths, thread_id)

        await cl.Message(
            content=f"Processed {len(files)} PDF(s). You can now ask me to generate a document."
        ).send()

    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()


@cl.on_message
async def on_message(message: cl.Message):
    conversation_history = cl.user_session.get("conversation_history")
    conversation_history.append(f"User: {message.content}")
    cl.user_session.set("conversation_history", conversation_history)
    
    graph = cl.user_session.get("graph")
    thread_id = cl.user_session.get("thread_id")
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create initial input with the user's message
    initial_input = {
        "request": message.content,
        "thread_id": thread_id,
        "conversation_history": conversation_history
    }

    # Run the graph and get the final state
    async for _ in graph.astream(initial_input, config):
        pass

    final_state = await graph.aget_state(config)
    
    # Process the final state
    if not final_state:
        await cl.Message(content="Something went wrong, the graph execution ended unexpectedly.").send()
        return

    # If we need more information from the user
    if final_state.values.get('missing_fields'):
        follow_up = final_state.values.get('follow_up_question')
        print("hiiiiiiiiiiiii follow_up: ", follow_up)
        if follow_up:
            conversation_history.append(f"AI: {follow_up}")
            await cl.Message(content=follow_up).send()
        return

    # If we have a generated document
    if final_state.values.get('generated_document'):
        doc = final_state.values['generated_document']
        response = "Here is the generated document:"
        conversation_history.append(f"AI: {response}")
        await cl.Message(
            content=f"{response}\n\n{doc}",
            elements=[cl.File(name="generated_document.txt", content=doc.encode(), display="inline")]
        ).send()
        return

    # If we reach here, something unexpected happened
    await cl.Message(content="An unexpected error occurred during processing.").send()