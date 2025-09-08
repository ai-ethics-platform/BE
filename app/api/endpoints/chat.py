from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.core.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse


router = APIRouter()


@router.post("/chat/with-prompt", response_model=ChatResponse)
async def chat_with_prompt(payload: ChatRequest, db: AsyncSession = Depends(get_db)) -> Any:
    try:
        # Lazy import to avoid startup dependency if key missing
        from openai import OpenAI
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI SDK import error: {e}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)

    try:
        resp = client.responses.create(
            prompt={"id": payload.prompt.id, "version": payload.prompt.version},
            input=payload.input,
            input_variables=payload.context or {},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI call failed: {e}")

    # Extract plain text from response
    text_parts: list[str] = []
    try:
        for item in getattr(resp, "output", []) or []:
            for c in getattr(item, "content", []) or []:
                if getattr(c, "type", "") == "output_text":
                    text_parts.append(getattr(c, "text", ""))
    except Exception:
        pass

    text = "".join(text_parts).strip()
    if not text:
        text = ""

    return ChatResponse(step=payload.step, text=text, raw=getattr(resp, "model_dump", lambda: None)())


