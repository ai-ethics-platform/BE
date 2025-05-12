import os
from typing import Any, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.core.config import settings
from app.services import audio_service

router = APIRouter()


@router.post("/upload", response_model=schemas.AudioUpload)
async def upload_audio(
    file: UploadFile = File(...),
    room_id: int = None,
    round_id: int = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    음성 파일 업로드
    """
    # 파일 크기 제한 확인
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    await file.seek(0)
    
    max_size = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024  # MB to bytes
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기는 {settings.MAX_AUDIO_SIZE_MB}MB를 초과할 수 없습니다",
        )
    
    # 파일 확장자 확인
    if not file.filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.webm')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원되지 않는 파일 형식입니다. mp3, wav, ogg, m4a, webm 형식만 지원합니다.",
        )
    
    # 저장 디렉토리 확인 및 생성
    os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
    
    # 파일 저장 및 DB 등록
    audio_file = await audio_service.save_audio(
        file=file,
        user_id=current_user.id,
        room_id=room_id,
        round_id=round_id
    )
    
    return audio_file


@router.get("/recordings", response_model=List[schemas.AudioFile])
async def list_recordings(
    room_id: int = None,
    round_id: int = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    사용자의 녹음 파일 목록 조회
    """
    recordings = await audio_service.get_user_recordings(
        user_id=current_user.id,
        room_id=room_id,
        round_id=round_id
    )
    return recordings


@router.post("/transcribe", response_model=schemas.Transcription)
async def transcribe_audio(
    transcribe_data: schemas.TranscribeRequest,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    음성 파일 텍스트 변환 (STT)
    """
    # 파일 존재 확인
    audio_file = await audio_service.get_audio_file(transcribe_data.audio_id)
    if not audio_file or audio_file.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="음성 파일을 찾을 수 없습니다",
        )
    
    # 텍스트 변환 요청
    transcription = await audio_service.transcribe_audio(audio_file)
    return transcription 