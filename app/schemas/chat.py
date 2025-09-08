from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ChatPromptRef(BaseModel):
    id: str = Field(..., description="Playground Prompt ID (pmpt_...)" )
    version: str = Field(..., description="Published prompt version string")


class ChatRequest(BaseModel):
    step: Optional[str] = Field(default=None, description="Current flow step identifier")
    input: str = Field(..., description="User input text")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Variables to fill prompt")
    prompt: ChatPromptRef


class ChatResponse(BaseModel):
    step: Optional[str] = None
    text: str
    raw: Optional[Dict[str, Any]] = None


