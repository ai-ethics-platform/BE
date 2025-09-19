from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChatSessionBase(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    current_step: str = Field(default="topic", description="Current step in the conversation flow")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context data from previous steps")


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionUpdate(BaseModel):
    current_step: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatSessionResponse(ChatSessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        extra = "forbid"


class MultiStepChatRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    user_input: str = Field(..., description="User's input text")
    step: Optional[str] = Field(default=None, description="Specific step to execute (optional)")


class MultiStepChatResponse(BaseModel):
    session_id: str
    current_step: str
    response_text: str
    context: Optional[Dict[str, Any]] = None
    next_step: Optional[str] = None
    is_complete: bool = False
