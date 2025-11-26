import logging
from fastapi import FastAPI, Security
from fastapi.responses import JSONResponse, StreamingResponse
import uuid
from agent_logic import setup_agent
from models import AgentRequest, OpenAIChatRequest
from fastapi.security import APIKeyHeader
import json
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


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



# --- Helper function for streaming ---
async def stream_agent_response(user_prompt: str, model_name: str):
    """
    An async generator that streams the agent's final response chunks.
    """
    response_id = f"chatcmpl-{uuid.uuid4()}"
    
    # Use astream_log for more granular control if needed, but astream is simpler for final output
    async for chunk in agent_executor.astream({"input": user_prompt}):
        # The agent streams different types of chunks (thoughts, tool outputs, etc.)
        # We only want to stream the final answer parts, which are in the 'output' key.
        if "output" in chunk:
            # Format the chunk in the OpenAI SSE (Server-Sent Events) format
            chunk_payload = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": 1677652288,
                "model": model_name,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": chunk["output"],
                    },
                    "finish_reason": None
                }]
            }
            # The 'data: ' prefix and '\n\n' suffix are required by the SSE standard
            yield f"data: {json.dumps(chunk_payload)}\n\n"

    # After the loop finishes, send the final [DONE] message
    yield "data: [DONE]\n\n"


# --- Endpoint 2: REPLACED with Streaming-Capable Version ---
@app.post("/v1/chat/completions")
async def chat_completions(request: OpenAIChatRequest, api_key: str = Security(api_key_header)):
    """
    Emulates the OpenAI Chat Completions API. Handles both streaming and non-streaming.
    """
    if not request.messages:
        return JSONResponse(status_code=400, content={"error": "No messages provided."})

    user_prompt = request.messages[-1].content
    logging.info(f"OpenAI compatible endpoint received prompt: '{user_prompt}'")

    try:
        # Check if the client requested a streaming response
        if request.stream:
            # Return a StreamingResponse that uses our async generator
            return StreamingResponse(
                stream_agent_response(user_prompt, request.model),
                media_type="text/event-stream"
            )
        else:
            # Use the original non-streaming logic
            result = await agent_executor.ainvoke({"input": user_prompt})
            response_content = result.get('output', "Sorry, I encountered an error.")
            return {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion",
                "created": 1677652288,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": response_content},
                    "finish_reason": "stop"
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
    except Exception as e:
        logging.error(f"Error in OpenAI compatible endpoint: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

