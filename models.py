# /itsm_agent/models.py

from pydantic import BaseModel
from typing import List, Dict, Optional

# Model for the direct API endpoint (used by ServiceNow)
class AgentRequest(BaseModel):
    prompt: str

# Models to emulate the OpenAI API for GUI compatibility (like LibreChat)
class ChatMessage(BaseModel):
    role: str
    content: str

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    # Add other OpenAI params as needed, e.g., temperature, stream