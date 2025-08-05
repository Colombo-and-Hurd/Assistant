import sys
import os
import uuid

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import chainlit as cl
from backend.src.graph import create_graph

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

    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")

    if message.elements:
        files = [file for file in message.elements if "application/pdf" in file.mime]
        
        if files:
            file_paths = []
            for file in files:
                content = file.content
                if content is None and file.path:
                    with open(file.path, "rb") as f:
                        content = f.read()

                if content:
                    file_path = os.path.join(UPLOAD_DIR, f"{thread_id}_{file.name}")
                    with open(file_path, "wb") as f:
                        f.write(content)
                    file_paths.append(file_path)
                else:
                    await cl.Message(content=f"Could not read content of file {file.name}.").send()

            agent.process_pdfs(file_paths, thread_id)

            await cl.Message(
                content=f"Processed {len(files)} PDF(s)."
            ).send()
            
            if not message.content.strip():
                return

    conversation_history = cl.user_session.get("conversation_history")
    conversation_history.append(f"User: {message.content}")
    cl.user_session.set("conversation_history", conversation_history)
    
    graph = cl.user_session.get("graph")
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_input = {
        "request": message.content,
        "thread_id": thread_id,
        "conversation_history": conversation_history,
        "files": [file.name for file in message.elements if "application/pdf" in file.mime]
    }

    async for _ in graph.astream(initial_input, config):
        pass
    
    final_state = await graph.aget_state(config)
    
    if not final_state:
        await cl.Message(content="Something went wrong, the graph execution ended unexpectedly.").send()
        return

    if final_state.values.get('missing_fields'):
        print("---MISSING FIELDS---", final_state.values.get('missing_fields'))
        follow_up = final_state.values.get('follow_up_question')
        if follow_up:
            conversation_history.append(f"AI: {follow_up}")
            await cl.Message(content=follow_up).send()
        return

    if final_state.values.get('generated_document'):
        doc = final_state.values['generated_document']
        response = "Here is the generated document:"
        conversation_history.append(f"AI: {response}")
        await cl.Message(
            content=f"{response}\n\n{doc}",
            elements=[cl.File(name="generated_document.txt", content=doc.encode(), display="inline")]
        ).send()
        return
        
    if final_state.values.get('conversational_response'):
        response = final_state.values['conversational_response']
        conversation_history.append(f"AI: {response}")
        await cl.Message(content=response).send()
        return

    await cl.Message(content="An unexpected error occurred during processing.").send()
