# /itsm_agent/main.py

import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from agent_logic import setup_agent
from models import AgentRequest, OpenAIChatRequest

# --- App Initialization ---
app = FastAPI(
    title="AIOps Agent",
    description="An AI agent for summarizing and suggesting procedures for NOC tickets.",
    version="1.0.0"
)

# Initialize the agent once when the application starts
agent_executor = setup_agent()

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "AIOps Agent is running."}


# --- Endpoint 1: Direct API for Programmatic Access (e.g., ServiceNow) ---
@app.post("/invoke")
async def invoke_agent(request: AgentRequest):
    """
    Receives a prompt and uses the agent to generate a response.
    This is the primary endpoint for services like ServiceNow.
    """
    try:
        logging.info(f"Invoking agent with prompt: '{request.prompt}'")
        # The agent expects a dictionary with an "input" key
        result = await agent_executor.ainvoke({"input": request.prompt})
        return {"response": result.get('output')}
    except Exception as e:
        logging.error(f"Error invoking agent: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- Endpoint 2: OpenAI-Compatible API for GUIs (e.g., LibreChat) ---
@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest):
    """
    Emulates the OpenAI Chat Completions API to be compatible with various GUIs.
    It takes the last user message as the input for the agent.
    """
    if not request.messages:
        return JSONResponse(status_code=400, content={"error": "No messages provided."})

    # Extract the last user message as the prompt for our agent
    user_prompt = request.messages[-1].content
    logging.info(f"OpenAI compatible endpoint received prompt: '{user_prompt}'")

    try:
        # Invoke the agent with the extracted prompt
        result = await agent_executor.ainvoke({"input": user_prompt})
        response_content = result.get('output', "Sorry, I encountered an error.")

        # Format the response to match the OpenAI API structure
        return {
            "id": "chatcmpl-mock-id",
            "object": "chat.completion",
            "created": 1677652288,
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content,
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0, # You can implement token counting if needed
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
    except Exception as e:
        logging.error(f"Error in OpenAI compatible endpoint: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})