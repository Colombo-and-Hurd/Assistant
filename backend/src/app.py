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

    except Exception as e:
        await cl.Message(content=f"An error occurred: {e}").send()


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    thread_id = cl.user_session.get("thread_id")

    if message.elements:
        files = [file for file in message.elements if "application/pdf" in file.mime]
        
        if files:
            async with cl.Step(name="Processing PDFs", type="processing") as step:
                step.input = f"Processing {len(files)} PDF files"
                file_paths = []
                
                for idx, file in enumerate(files, 1):
                    await step.stream_token(f"\nProcessing file {idx}/{len(files)}: {file.name}")
                    content = file.content
                    if content is None and file.path:
                        with open(file.path, "rb") as f:
                            content = f.read()

                    if content:
                        file_path = os.path.join(UPLOAD_DIR, f"{thread_id}_{file.name}")
                        with open(file_path, "wb") as f:
                            f.write(content)
                        file_paths.append(file_path)
                        await step.stream_token(" ✓")
                    else:
                        await step.stream_token(" ✗")
                        await cl.Message(content=f"Could not read content of file {file.name}.").send()

                await step.stream_token("\nAnalyzing PDF contents...")
                agent.process_pdfs(file_paths, thread_id)
                step.output = f"Successfully processed {len(files)} PDF(s)"

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
        "conversation_history": conversation_history
    }

    async with cl.Step(name="Processing Request", type="run") as step:
        step.input = message.content
        await step.stream_token("Analyzing your request...")
        
        async for _ in graph.astream(initial_input, config):
            await step.stream_token(".")
        
        final_state = await graph.aget_state(config)
        
        if not final_state:
            step.output = "Error: Graph execution ended unexpectedly"
            await cl.Message(content="Something went wrong, the graph execution ended unexpectedly.").send()
            return

        if final_state.values.get('missing_fields'):
            follow_up = final_state.values.get('follow_up_question')
            if follow_up:
                step.output = "Additional information needed"
                conversation_history.append(f"AI: {follow_up}")
                await cl.Message(content=follow_up).send()
            return

        if final_state.values.get('generated_document'):
            async with cl.Step(name="Document Generation", type="generation") as doc_step:
                doc = final_state.values['generated_document']
                doc_step.input = "Generating final document"
                await doc_step.stream_token("Formatting document...")
                doc_step.output = "✓ Document ready"
                
            response = "Here is the generated document:"
            conversation_history.append(f"AI: {response}")
            await cl.Message(
                content=f"{response}\n\n{doc}",
                elements=[cl.File(name="generated_document.txt", content=doc.encode(), display="inline")]
            ).send()
            return

    # If we reach here, something unexpected happened
    await cl.Message(content="An unexpected error occurred during processing.").send()