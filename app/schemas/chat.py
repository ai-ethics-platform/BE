from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ChatPromptRef(BaseModel):
    id: Optional[str] = Field(default=None, description="Playground Prompt ID (pmpt_...) - optional if template provided")
    version: Optional[str] = Field(default=None, description="Published prompt version string (optional: latest if omitted)")
    variables: Optional[Dict[str, Any]] = Field(default=None, description="Variables required by the saved prompt")
    template: Optional[str] = Field(default=None, description="Prompt template string (managed by frontend) - use {variable_name} for variables")


class ChatRequest(BaseModel):
    step: Optional[str] = Field(default=None, description="Current flow step identifier")
    input: str = Field(..., description="User input text")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Variables to fill prompt (fallback if prompt.variables absent)")
    prompt: Optional[ChatPromptRef] = Field(default=None, description="Saved prompt reference from Playground (optional if server-mapped)")


class ImageRequest(BaseModel):
    step: Optional[str] = Field(default="image", description="Image step identifier")
    input: str = Field(..., description="Image prompt text")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Variables to fill prompt (fallback if prompt.variables absent)")
    prompt: Optional[ChatPromptRef] = Field(default=None, description="Saved prompt reference from Playground (optional if using direct input)")
    size: Optional[str] = Field(default="1024x1024", description="Image size, e.g., 512x512, 1024x1024")


class ChatResponse(BaseModel):
    step: Optional[str] = None
    text: str
    raw: Optional[Dict[str, Any]] = None


class GeneratedImage(BaseModel):
    """LangChain으로 파싱된 이미지 생성 정보"""
    description: str = Field(..., description="상세한 이미지 설명")
    style: Optional[str] = Field(None, description="예술 스타일이나 톤")
    size: Optional[str] = Field(None, description="이미지 크기")
    reasoning: Optional[str] = Field(None, description="이미지가 사용자 의도에 맞는 이유")


class ImageResponse(BaseModel):
    step: Optional[str] = Field(default="image")
    image_data_url: str = Field(..., description="생성된 이미지 URL (로컬 또는 원격)")
    model: str = Field(default="dall-e-3")
    size: str = Field(default="1024x1024")
    parsed_result: Optional[Dict[str, Any]] = Field(None, description="LangChain으로 파싱된 이미지 생성 정보 (description, style, reasoning 등)")


