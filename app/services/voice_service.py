# app/services/voice_service.py
from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
import secrets
import string
import os
from datetime import datetime, timedelta

from app import models, schemas
from app.core.deps import get_db


class VoiceService:
    
    @staticmethod
    async def create_voice_session(
        db: AsyncSession,
        room_code: str,
        creator_id: Optional[int],
        creator_nickname: str
    ) -> models.VoiceSession:
        """음성 세션 생성"""
        
        # 방 조회
        room = await db.execute(
            select(models.Room).where(models.Room.room_code == room_code)
        )
        room = room.scalar_one_or_none()
        
        if not room:
            raise ValueError("존재하지 않는 방입니다.")
        
        if not room.is_active:
            raise ValueError("비활성화된 방입니다.")
        
        # 고유한 세션 ID 생성
        session_id = VoiceService._generate_session_id()
        
        # 음성 세션 생성
        voice_session = models.VoiceSession(
            room_id=room.id,
            session_id=session_id,
            is_active=True
        )
        
        db.add(voice_session)
        await db.flush()  # ID 생성을 위해 flush
        
        # 생성자를 음성 세션에 자동 참가시킴
        participant = models.VoiceParticipant(
            voice_session_id=voice_session.id,
            user_id=creator_id,
            guest_id=None if creator_id else creator_nickname.replace("게스트_", ""),
            nickname=creator_nickname,
            is_mic_on=False,
            is_speaking=False,
            is_connected=True
        )
        
        db.add(participant)
        await db.commit()
        await db.refresh(voice_session)
        
        return voice_session
    
    @staticmethod
    async def get_voice_session_by_room_code(
        db: AsyncSession,
        room_code: str
    ) -> Optional[models.VoiceSession]:
        """방 코드로 음성 세션 조회"""
        result = await db.execute(
            select(models.VoiceSession)
            .join(models.Room)
            .options(selectinload(models.VoiceSession.participants))
            .where(
                and_(
                    models.Room.room_code == room_code,
                    models.VoiceSession.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    def _generate_session_id() -> str:
        """고유한 세션 ID 생성"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
    
    @staticmethod
    async def get_voice_session_by_id(
        db: AsyncSession,
        session_id: str
    ) -> Optional[models.VoiceSession]:
        """세션 ID로 음성 세션 조회"""
        result = await db.execute(
            select(models.VoiceSession)
            .options(selectinload(models.VoiceSession.participants))
            .where(models.VoiceSession.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def join_voice_session(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[int],
        guest_id: Optional[str],
        nickname: str
    ) -> Union[models.VoiceParticipant, List[models.VoiceParticipant]]:
        """음성 세션 참가"""
        
        # 세션 조회
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            raise ValueError("존재하지 않는 음성 세션입니다.")
        
        if not voice_session.is_active:
            raise ValueError("비활성화된 음성 세션입니다.")
        
        # 현재 참가자 수 확인
        current_participants = await VoiceService.get_session_participants(db=db, session_id=session_id)
        
        # 이미 참가 중인지 확인
        existing_participant = await db.execute(
            select(models.VoiceParticipant).where(
                and_(
                    models.VoiceParticipant.voice_session_id == voice_session.id,
                    models.VoiceParticipant.user_id == user_id if user_id else 
                    models.VoiceParticipant.guest_id == guest_id
                )
            )
        )
        existing_participant = existing_participant.scalar_one_or_none()
        if existing_participant:
            # 이미 참여중이면 기존 참가자 반환
            return existing_participant
        
        # 3명이 꽉 찼는지 확인
        if len(current_participants) >= 3:
            # 꽉 찼으면 현재 참가자 목록 반환
            return current_participants
        
        # 참가자 추가
        participant = models.VoiceParticipant(
            voice_session_id=voice_session.id,
            user_id=user_id,
            guest_id=guest_id,
            nickname=nickname,
            is_mic_on=False,
            is_speaking=False,
            is_connected=True
        )
        
        db.add(participant)
        await db.commit()
        await db.refresh(participant)
        
        return participant
    
    @staticmethod
    async def update_voice_status(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[int],
        guest_id: Optional[str],
        is_mic_on: bool,
        is_speaking: bool = False
    ) -> models.VoiceParticipant:
        """음성 상태 업데이트"""
        
        # 세션 조회
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            raise ValueError("존재하지 않는 음성 세션입니다.")
        
        # 참가자 조회
        participant_query = select(models.VoiceParticipant).where(
            and_(
                models.VoiceParticipant.voice_session_id == voice_session.id,
                models.VoiceParticipant.user_id == user_id if user_id else 
                models.VoiceParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("음성 세션에 참가하지 않은 사용자입니다.")
        
        # 상태 업데이트
        participant.is_mic_on = is_mic_on
        participant.is_speaking = is_speaking
        participant.last_activity = datetime.utcnow()
        
        await db.commit()
        await db.refresh(participant)
        
        return participant
    
    @staticmethod
    async def leave_voice_session(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> bool:
        """음성 세션 퇴장"""
        
        # 세션 조회
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            raise ValueError("존재하지 않는 음성 세션입니다.")
        
        # 참가자 조회
        participant_query = select(models.VoiceParticipant).where(
            and_(
                models.VoiceParticipant.voice_session_id == voice_session.id,
                models.VoiceParticipant.user_id == user_id if user_id else 
                models.VoiceParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("음성 세션에 참가하지 않은 사용자입니다.")
        
        # 참가자 삭제
        await db.delete(participant)
        
        # 세션에 참가자가 없으면 세션 비활성화
        remaining_participants = await db.execute(
            select(models.VoiceParticipant).where(
                models.VoiceParticipant.voice_session_id == voice_session.id
            )
        )
        if not remaining_participants.scalars().all():
            voice_session.is_active = False
            voice_session.ended_at = datetime.utcnow()
        
        await db.commit()
        
        return True
    
    @staticmethod
    async def start_recording(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> models.VoiceParticipant:
        """녹음 시작"""
        
        # 세션 조회
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            raise ValueError("존재하지 않는 음성 세션입니다.")
        
        # 참가자 조회
        participant_query = select(models.VoiceParticipant).where(
            and_(
                models.VoiceParticipant.voice_session_id == voice_session.id,
                models.VoiceParticipant.user_id == user_id if user_id else 
                models.VoiceParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("음성 세션에 참가하지 않은 사용자입니다.")
        
        # 이미 녹음 중인지 확인
        if participant.recording_started_at and not participant.recording_ended_at:
            raise ValueError("이미 녹음 중입니다.")
        
        # 녹음 파일 경로 생성
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        user_identifier = str(user_id) if user_id else guest_id
        recording_filename = f"recording_{user_identifier}_{timestamp}.wav"
        recording_path = f"recordings/{recording_filename}"
        
        # 녹음 디렉토리 생성
        os.makedirs("recordings", exist_ok=True)
        
        # 녹음 상태 업데이트
        participant.recording_file_path = recording_path
        participant.recording_started_at = datetime.utcnow()
        participant.recording_ended_at = None
        
        await db.commit()
        await db.refresh(participant)
        
        return participant
    
    @staticmethod
    async def stop_recording(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> tuple[models.VoiceParticipant, int]:
        """녹음 종료"""
        
        # 세션 조회
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            raise ValueError("존재하지 않는 음성 세션입니다.")
        
        # 참가자 조회
        participant_query = select(models.VoiceParticipant).where(
            and_(
                models.VoiceParticipant.voice_session_id == voice_session.id,
                models.VoiceParticipant.user_id == user_id if user_id else 
                models.VoiceParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("음성 세션에 참가하지 않은 사용자입니다.")
        
        # 녹음 중인지 확인
        if not participant.recording_started_at or participant.recording_ended_at:
            raise ValueError("녹음 중이 아닙니다.")
        
        # 녹음 종료 시간 설정
        participant.recording_ended_at = datetime.utcnow()
        
        # 녹음 시간 계산 (초 단위)
        duration = int((participant.recording_ended_at - participant.recording_started_at).total_seconds())
        
        await db.commit()
        await db.refresh(participant)
        
        return participant, duration
    
    @staticmethod
    async def upload_recording(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[int],
        guest_id: Optional[str],
        file_path: str
    ) -> models.VoiceRecording:
        """녹음 파일 업로드"""
        
        # 세션 조회
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            raise ValueError("존재하지 않는 음성 세션입니다.")
        
        # 파일 크기 계산
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # 음성 녹음 기록 생성
        voice_recording = models.VoiceRecording(
            voice_session_id=voice_session.id,
            user_id=user_id,
            guest_id=guest_id,
            file_path=file_path,
            file_size=file_size,
            uploaded_at=datetime.utcnow()
        )
        
        db.add(voice_recording)
        await db.commit()
        await db.refresh(voice_recording)
        
        return voice_recording

    @staticmethod
    async def get_session_participants(
        db: AsyncSession,
        session_id: str
    ) -> List[models.VoiceParticipant]:
        """세션의 모든 참가자 조회"""
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            return []
        
        return voice_session.participants

    @staticmethod
    async def get_participant_by_user(
        db: AsyncSession,
        session_id: str,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> Optional[models.VoiceParticipant]:
        """사용자별 참가자 정보 조회"""
        voice_session = await VoiceService.get_voice_session_by_id(db=db, session_id=session_id)
        if not voice_session:
            return None
        
        participant_query = select(models.VoiceParticipant).where(
            and_(
                models.VoiceParticipant.voice_session_id == voice_session.id,
                models.VoiceParticipant.user_id == user_id if user_id else 
                models.VoiceParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        return result.scalar_one_or_none()


# 서비스 인스턴스
voice_service = VoiceService()