from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ChatPromptRef(BaseModel):
    id: str = Field(..., description="Playground Prompt ID (pmpt_...)" )
    version: Optional[str] = Field(default=None, description="Published prompt version string (optional: latest if omitted)")
    variables: Optional[Dict[str, Any]] = Field(default=None, description="Variables required by the saved prompt")


class ChatRequest(BaseModel):
    step: Optional[str] = Field(default=None, description="Current flow step identifier")
    input: str = Field(..., description="User input text")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Variables to fill prompt (fallback if prompt.variables absent)")
    prompt: Optional[ChatPromptRef] = Field(default=None, description="Saved prompt reference from Playground (optional if server-mapped)")


class ImageRequest(BaseModel):
    step: Optional[str] = Field(default="image", description="Image step identifier")
    input: str = Field(..., description="Image prompt text")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context to persist or audit")
    size: Optional[str] = Field(default="1024x1024", description="Image size, e.g., 512x512, 1024x1024")


class ChatResponse(BaseModel):
    step: Optional[str] = None
    text: str
    raw: Optional[Dict[str, Any]] = None


class ImageResponse(BaseModel):
    step: Optional[str] = Field(default="image")
    image_data_url: str
    model: str = Field(default="dall-e-3")
    size: str = Field(default="1024x1024")


