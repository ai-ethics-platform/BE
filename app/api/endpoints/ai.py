from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.services import ai_service

router = APIRouter()


@router.post("/analyze-conversation", response_model=schemas.AIAnalysis)
async def analyze_conversation(
    analysis_request: schemas.AnalysisRequest,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    대화 내용 분석 및 AI 피드백 생성
    """
    # 대화 내용 분석
    analysis = await ai_service.analyze_conversation(
        transcription_id=analysis_request.transcription_id,
        user_id=current_user.id,
    )
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="분석할 대화 내용을 찾을 수 없습니다",
        )
    
    return analysis


@router.get("/feedback/{game_id}", response_model=schemas.AIFeedback)
async def get_game_feedback(
    game_id: int,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    게임 세션에 대한 AI 피드백 조회
    """
    feedback = await ai_service.get_game_feedback(
        game_id=game_id,
        user_id=current_user.id,
    )
    
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 게임에 대한 피드백을 찾을 수 없습니다",
        )
    
    return feedback


@router.post("/generate-response", response_model=schemas.AIResponse)
async def generate_ai_response(
    response_request: schemas.AIResponseRequest,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    AI 응답 생성 (GPT 기반)
    """
    response = await ai_service.generate_response(
        prompt=response_request.prompt,
        context=response_request.context,
        game_id=response_request.game_id,
    )
    
    return response 