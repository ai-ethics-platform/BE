# app/api/audio_upload.py
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import shutil
import os
from datetime import datetime

from app.core.deps import get_db, get_current_user
from app.services.voice_service import voice_service
from app.models.voice import VoiceRecording

router = APIRouter()

UPLOAD_DIR = "recordings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload_audio")
async def upload_audio(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_id = current_user.id

    # 파일 경로 설정
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{user_id}_{timestamp}.wav"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # 파일 저장
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # DB 업데이트
    participant = await voice_service.get_participant_by_user(
        db=db, session_id=session_id, user_id=user_id, guest_id=None
    )

    if not participant:
        raise HTTPException(status_code=404, detail="참가자 정보를 찾을 수 없습니다.")

    participant.recording_file_path = file_path
    await db.flush()
    # VoiceRecording insert
    new_recording = VoiceRecording(
        voice_session_id=participant.voice_session_id,
        user_id=user_id,
        guest_id=None,
        file_path=file_path,
        file_size=os.path.getsize(file_path),
        duration=None,
        uploaded_at=datetime.utcnow(),
    )
    db.add(new_recording)
    await db.commit()

    return {
        "message": "파일 업로드 성공",
        "file_path": file_path
    }
