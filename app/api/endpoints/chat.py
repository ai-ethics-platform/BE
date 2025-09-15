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

    # Process prompt if provided
    final_prompt = payload.input
    if payload.prompt:
        # Resolve variables: prefer prompt.variables > context > {}
        variables = payload.prompt.variables or payload.context or {}
        
        prompt_obj = {"id": payload.prompt.id}
        if payload.prompt.version:
            prompt_obj["version"] = payload.prompt.version
        if variables:
            prompt_obj["variables"] = variables

        try:
            # Get the processed prompt from OpenAI Playground
            resp = client.responses.create(
                prompt=prompt_obj,
                input=payload.input,
            )
            
            # Extract the processed prompt text
            processed_parts = []
            try:
                for item in getattr(resp, "output", []) or []:
                    for c in getattr(item, "content", []) or []:
                        if getattr(c, "type", "") == "output_text":
                            processed_parts.append(getattr(c, "text", ""))
            except Exception:
                pass
            
            processed_text = "".join(processed_parts).strip()
            if processed_text:
                final_prompt = processed_text
                
        except Exception as e:
            # If prompt processing fails, fall back to direct input
            pass

    size = payload.size or "1024x1024"
    try:
        img = client.images.generate(
            model="dall-e-3",
            prompt=final_prompt,
            size=size,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI image call failed: {e}")

    try:
        image_url = img.data[0].url
        if not image_url:
            raise HTTPException(status_code=502, detail="Empty image URL from OpenAI")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Invalid image response from OpenAI: {e}")

    # OpenAI 이미지를 로컬에 다운로드해서 저장 (만료 방지)
    import httpx
    from datetime import datetime
    
    try:
        # 이미지 다운로드
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_data = response.content
        
        # 로컬 저장소에 저장
        os.makedirs("static/generated_images", exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"dalle_{timestamp}_{os.urandom(4).hex()}.png"
        file_path = os.path.join("static/generated_images", filename)
        
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        # 로컬 URL로 반환
        local_url = f"/static/generated_images/{filename}"
        
    except Exception as e:
        # 다운로드 실패 시 원본 URL 사용
        local_url = image_url

    return ImageResponse(step=payload.step, image_data_url=local_url, model="dall-e-3", size=size)


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


