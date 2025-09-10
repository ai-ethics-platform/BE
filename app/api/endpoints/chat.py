from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.core.deps import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ImageRequest, ImageResponse
from app.schemas.chat_session import MultiStepChatRequest, MultiStepChatResponse
from app.services.chat_service import chat_service


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

    # Resolve variables: prefer prompt.variables > context > {}
    prompt_obj = None
    if payload.prompt:
        prompt_obj = {"id": payload.prompt.id}
        if payload.prompt.version:
            prompt_obj["version"] = payload.prompt.version
        variables = payload.prompt.variables or payload.context or {}
        if variables:
            prompt_obj["variables"] = variables
    else:
        # Backward compatibility: allow server-side mapping via step + context
        if not payload.step:
            raise HTTPException(status_code=400, detail="Either prompt or step must be provided")
        prompt_obj = {"id": None}

    try:
        resp = client.responses.create(
            prompt=prompt_obj,
            input=payload.input,
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


@router.post("/chat/image", response_model=ImageResponse)
async def generate_image(payload: ImageRequest) -> Any:
    try:
        from openai import OpenAI
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI SDK import error: {e}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)

    size = payload.size or "1024x1024"
    try:
        img = client.images.generate(
            model="gpt-image-1",
            prompt=payload.input,
            size=size,
            response_format="b64_json",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI image call failed: {e}")

    try:
        b64 = img.data[0].b64_json
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid image response from OpenAI")

    data_url = f"data:image/png;base64,{b64}"
    return ImageResponse(step=payload.step, image_data_url=data_url, model="gpt-image-1", size=size)


@router.post("/chat/multi-step", response_model=MultiStepChatResponse)
async def multi_step_chat(
    request: MultiStepChatRequest, 
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    다단계 챗봇 API
    
    - session_id: 세션 식별자 (프론트엔드에서 생성)
    - user_input: 사용자 입력
    - step: 특정 단계 실행 (선택사항, 없으면 현재 단계에서 진행)
    
    단계 순서: topic -> question -> situation -> discussion -> conclusion
    """
    try:
        response = await chat_service.process_multi_step_chat(db, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/chat/session/{session_id}")
async def get_session_info(session_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    """세션 정보 조회"""
    try:
        session = await chat_service.get_or_create_session(db, session_id)
        return {
            "session_id": session.session_id,
            "current_step": session.current_step,
            "context": session.context,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {e}")


@router.delete("/chat/session/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)) -> Any:
    """세션 삭제"""
    try:
        from sqlalchemy import delete
        from app.models.chat_session import ChatSession
        
        await db.execute(
            delete(ChatSession).where(ChatSession.session_id == session_id)
        )
        await db.commit()
        
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {e}")


