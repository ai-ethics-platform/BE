from typing import List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import random

from app import models, schemas
from app.core.deps import get_db


class RoomService:
    
    @staticmethod
    async def create_public_room(
        db: AsyncSession,
        room_data: schemas.RoomCreatePublic,
        creator_id: Optional[int],
        creator_nickname: str
    ) -> models.Room:
        """공개 방 생성"""
        
        # 방 코드 결정
        if room_data.custom_room_code:
            # 6자리 숫자 유효성 검사
            if not (isinstance(room_data.custom_room_code, str) and room_data.custom_room_code.isdigit() and len(room_data.custom_room_code) == 6):
                raise ValueError("방 코드는 6자리 숫자여야 합니다.")
            # 중복 확인
            existing_room = await db.execute(
                select(models.Room).where(models.Room.room_code == room_data.custom_room_code)
            )
            if existing_room.scalar_one_or_none():
                raise ValueError(f"방 코드 '{room_data.custom_room_code}'는 이미 사용 중입니다.")
            
            room_code = room_data.custom_room_code
        else:
            # 랜덤 방 코드 생성
            room_code = await RoomService._generate_unique_room_code(db)
        
        # 방 생성
        db_room = models.Room(
            room_code=room_code,
            title=room_data.title,
            description=room_data.description,
            topic=room_data.topic,
            is_public=True,
            allow_random_matching=True,  # 기본값
            max_players=3,  # 고정값 3
            current_players=1,  # 생성자가 자동 입장
            created_by=creator_id  # 게스트의 경우 None
        )
        
        db.add(db_room)
        await db.flush()  # ID 생성을 위해 flush
        
        # 생성자를 방에 자동 입장시킴
        participant = models.RoomParticipant(
            room_id=db_room.id,
            user_id=creator_id,
            guest_id=None if creator_id else creator_nickname.replace("게스트_", ""),
            nickname=creator_nickname,
            is_ready=False,  # 처음에는 준비 상태가 아님
            is_host=True  # 생성자는 자동으로 방장
        )
        
        db.add(participant)
        await db.commit()
        await db.refresh(db_room)
        
        # 참가자 정보와 함께 방 정보 로드
        result = await db.execute(
            select(models.Room)
            .options(selectinload(models.Room.participants))
            .where(models.Room.id == db_room.id)
        )
        return result.scalar_one()
    
    @staticmethod
    async def _generate_unique_room_code(db: AsyncSession) -> str:
        """고유한 방 코드 생성"""
        max_attempts = 10
        for _ in range(max_attempts):
            room_code = models.Room.generate_room_code()
            
            # 중복 확인
            result = await db.execute(
                select(models.Room).where(models.Room.room_code == room_code)
            )
            if not result.scalar_one_or_none():
                return room_code
        
        raise Exception("방 코드 생성에 실패했습니다. 다시 시도해주세요.")
    
    @staticmethod
    async def get_room_by_code(db: AsyncSession, room_code: str) -> Optional[models.Room]:
        """방 코드로 방 조회"""
        result = await db.execute(
            select(models.Room)
            .options(selectinload(models.Room.participants))
            .where(models.Room.room_code == room_code)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_public_rooms(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[models.Room]:
        """공개 방 목록 조회"""
        result = await db.execute(
            select(models.Room)
            .where(
                and_(
                    models.Room.is_public == True,
                    models.Room.is_active == True,
                    models.Room.is_started == False
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(models.Room.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def join_room(
        db: AsyncSession,
        room_id: int,
        user_id: Optional[int],
        guest_id: Optional[str],
        nickname: str
    ) -> models.RoomParticipant:
        """방 입장"""
        
        # 방 존재 및 입장 가능 여부 확인
        room = await db.get(models.Room, room_id)
        if not room:
            raise ValueError("존재하지 않는 방입니다.")
        
        if not room.is_active:
            raise ValueError("비활성화된 방입니다.")
        
        if room.is_started:
            raise ValueError("이미 시작된 게임입니다.")
        
        if room.current_players >= room.max_players:
            raise ValueError("방이 가득 찼습니다.")
        
        # 이미 참가 중인지 확인
        existing_participant = await db.execute(
            select(models.RoomParticipant).where(
                and_(
                    models.RoomParticipant.room_id == room_id,
                    models.RoomParticipant.user_id == user_id if user_id else 
                    models.RoomParticipant.guest_id == guest_id
                )
            )
        )
        if existing_participant.scalar_one_or_none():
            raise ValueError("이미 참가 중인 방입니다.")
        
        # 참가자 추가
        participant = models.RoomParticipant(
            room_id=room_id,
            user_id=user_id,
            guest_id=guest_id,
            nickname=nickname,
            is_ready=False,  # 처음에는 준비 상태가 아님
            is_host=False  # 입장하는 사람은 방장이 아님
        )
        
        # 방 참가자 수 증가
        room.current_players += 1
        
        db.add(participant)
        await db.commit()
        await db.refresh(participant)
        
        return participant
    
    @staticmethod
    async def create_private_room(
        db: AsyncSession,
        room_data: schemas.RoomCreatePrivate,
        creator_id: Optional[int],
        creator_nickname: str
    ) -> models.Room:
        """비공개 방 생성"""
        # 방 코드 결정
        if room_data.custom_room_code:
            # 6자리 숫자 유효성 검사
            if not (isinstance(room_data.custom_room_code, str) and room_data.custom_room_code.isdigit() and len(room_data.custom_room_code) == 6):
                raise ValueError("방 코드는 6자리 숫자여야 합니다.")
            # 중복 확인
            existing_room = await db.execute(
                select(models.Room).where(models.Room.room_code == room_data.custom_room_code)
            )
            if existing_room.scalar_one_or_none():
                raise ValueError(f"방 코드 '{room_data.custom_room_code}'는 이미 사용 중입니다.")
            room_code = room_data.custom_room_code
        else:
            # 랜덤 방 코드 생성
            room_code = await RoomService._generate_unique_room_code(db)
        
        # 방 생성
        db_room = models.Room(
            room_code=room_code,
            title=room_data.title,
            description=room_data.description,
            topic=room_data.topic,
            is_public=False,  # 비공개 방
            allow_random_matching=True,  # 기본값
            max_players=3,  # 고정값 3
            current_players=1,  # 생성자가 자동 입장
            created_by=creator_id  # 게스트의 경우 None
        )
        
        db.add(db_room)
        await db.flush()  # ID 생성을 위해 flush
        
        # 생성자를 방에 자동 입장시킴
        participant = models.RoomParticipant(
            room_id=db_room.id,
            user_id=creator_id,
            guest_id=None if creator_id else creator_nickname.replace("게스트_", ""),
            nickname=creator_nickname,
            is_ready=False,  # 처음에는 준비 상태가 아님
            is_host=True  # 생성자는 자동으로 방장
        )
        
        db.add(participant)
        await db.commit()
        await db.refresh(db_room)
        
        # 참가자 정보와 함께 방 정보 로드
        result = await db.execute(
            select(models.Room)
            .options(selectinload(models.Room.participants))
            .where(models.Room.id == db_room.id)
        )
        return result.scalar_one()
    
    @staticmethod
    async def get_private_rooms(
        db: AsyncSession,
        user_id: Optional[int],
        skip: int = 0, 
        limit: int = 20
    ) -> List[models.Room]:
        """비공개 방 목록 조회 (본인이 생성한 방만)"""
        if not user_id:
            return []  # 게스트는 비공개 방 목록 조회 불가
            
        result = await db.execute(
            select(models.Room)
            .where(
                and_(
                    models.Room.is_public == False,
                    models.Room.is_active == True,
                    models.Room.created_by == user_id
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(models.Room.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_available_rooms_for_random_join(
        db: AsyncSession
    ) -> List[models.Room]:
        """입장 가능한 공개 방 목록 조회"""
        result = await db.execute(
            select(models.Room)
            .where(
                and_(
                    models.Room.is_public == True,
                    models.Room.is_active == True,
                    models.Room.is_started == False,
                    models.Room.current_players >= 1,  # 최소 1명 이상
                    models.Room.current_players < models.Room.max_players  # 자리가 남아있음
                )
            )
            .order_by(models.Room.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def toggle_ready_status(
        db: AsyncSession,
        room_code: str,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> tuple[models.RoomParticipant, models.Room, bool, Optional[datetime]]:
        """
        준비 상태 토글 및 게임 시작 체크
        Returns: (participant, room, game_starting, start_time)
        """
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        if not room.is_active:
            raise ValueError("비활성화된 방입니다.")
        
        if room.is_started:
            raise ValueError("이미 시작된 게임입니다.")
        
        # 참가자 조회
        participant_query = select(models.RoomParticipant).where(
            and_(
                models.RoomParticipant.room_id == room.id,
                models.RoomParticipant.user_id == user_id if user_id else 
                models.RoomParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")
        
        # 준비 상태 토글
        participant.is_ready = not participant.is_ready
        
        # 모든 참가자의 준비 상태 확인
        all_participants_query = select(models.RoomParticipant).where(
            models.RoomParticipant.room_id == room.id
        )
        all_participants_result = await db.execute(all_participants_query)
        all_participants = all_participants_result.scalars().all()
        
        # 3명이 모두 준비되었는지 확인
        ready_count = sum(1 for p in all_participants if p.is_ready)
        total_participants = len(all_participants)
        
        game_starting = False
        start_time = None
        
        if total_participants == 3 and ready_count == 3:
            # 모든 사람이 준비됨 - 게임 시작 예약
            game_starting = True
            start_time = datetime.utcnow() + timedelta(seconds=3)
            room.start_time = start_time
            
            # TODO: 여기서 WebSocket으로 모든 클라이언트에게 시작 알림 전송
            # 예시: await websocket_manager.broadcast_to_room(room_code, {
            #     "type": "game_starting",
            #     "start_time": start_time.isoformat(),
            #     "message": "3초 후 게임이 시작됩니다!"
            # })
        
        await db.commit()
        await db.refresh(participant)
        await db.refresh(room)
        
        # 업데이트된 방 정보 조회 (참가자 포함)
        updated_room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        
        return participant, updated_room, game_starting, start_time

    @staticmethod
    async def reset_room_status(
        db: AsyncSession,
        room_code: str
    ) -> models.Room:
        """
        방 상태 초기화 (테스트용)
        - is_started를 false로 변경
        - start_time을 null로 변경  
        - 모든 참가자의 is_ready를 false로 변경
        """
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        # 방 상태 초기화
        room.is_started = False
        room.start_time = None
        
        # 모든 참가자의 준비 상태 초기화
        await db.execute(
            update(models.RoomParticipant)
            .where(models.RoomParticipant.room_id == room.id)
            .values(is_ready=False)
        )
        
        await db.commit()
        await db.refresh(room)
        
        # 업데이트된 방 정보 조회 (참가자 포함)
        updated_room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        
        return updated_room

    @staticmethod
    async def leave_room(
        db: AsyncSession,
        room_code: str,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> tuple[str, int, bool, Optional[dict], bool]:
        """
        방 나가기
        Returns: (room_code, remaining_players, room_deleted, new_host_info, game_started)
        """
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        # 나가는 참가자 조회
        participant_query = select(models.RoomParticipant).where(
            and_(
                models.RoomParticipant.room_id == room.id,
                models.RoomParticipant.user_id == user_id if user_id else 
                models.RoomParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")
        
        # 방장이 나가는지 확인
        was_host = participant.is_host
        
        # 방장이 나가는 경우, 삭제 전에 승계할 사람을 미리 찾기
        new_host_info = None
        new_host = None
        
        if was_host:
            # 나가는 사람을 제외한 나머지 참가자들 조회 (입장 순서대로)
            remaining_participants_query = select(models.RoomParticipant).where(
                and_(
                    models.RoomParticipant.room_id == room.id,
                    models.RoomParticipant.id != participant.id  # 나가는 사람 제외
                )
            ).order_by(models.RoomParticipant.joined_at.asc())
            
            remaining_result = await db.execute(remaining_participants_query)
            remaining_participants = remaining_result.scalars().all()
            
            if remaining_participants:
                new_host = remaining_participants[0]
                new_host.is_host = True
                
                new_host_info = {
                    "id": new_host.id,
                    "nickname": new_host.nickname,
                    "user_id": new_host.user_id,
                    "guest_id": new_host.guest_id
                }
        
        # 참가자 삭제
        await db.delete(participant)
        
        # 방 참가자 수 감소
        room.current_players -= 1
        
        room_deleted = False
        
        # 방에 아무도 없으면 방 비활성화
        if room.current_players <= 0:
            room.is_active = False
            room_deleted = True
        
        await db.commit()
        
        return room_code, room.current_players, room_deleted, new_host_info, room.is_started

    @staticmethod
    async def assign_roles(
        db: AsyncSession,
        room_code: str
    ) -> List[schemas.RoleAssignment]:
        """
        방의 모든 참가자에게 역할을 랜덤 배정
        Returns: 역할 배정 결과 목록
        """
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        if not room.is_active:
            raise ValueError("비활성화된 방입니다.")
        
        if room.is_started:
            raise ValueError("이미 시작된 게임입니다.")
        
        # 방의 모든 참가자 조회
        participants_query = select(models.RoomParticipant).where(
            models.RoomParticipant.room_id == room.id
        )
        participants_result = await db.execute(participants_query)
        participants = participants_result.scalars().all()
        
        if len(participants) != 3:
            raise ValueError("역할 배정은 3명의 참가자가 모두 있어야 합니다.")
        
        # 사용 가능한 역할 ID 목록 (1, 2, 3)
        available_roles = [1, 2, 3]
        
        # 참가자들을 랜덤하게 섞기
        shuffled_participants = list(participants)
        random.shuffle(shuffled_participants)
        
        # 역할 배정
        assignments = []
        for i, participant in enumerate(shuffled_participants):
            role_id = available_roles[i]
            participant.role_id = role_id
            
            # 플레이어 ID 결정 (user_id 또는 guest_id)
            player_id = str(participant.user_id) if participant.user_id else participant.guest_id
            
            assignment = schemas.RoleAssignment(
                player_id=player_id,
                role_id=role_id,
                role_name=schemas.ROLE_DEFINITIONS[role_id]
            )
            assignments.append(assignment)
        
        # 데이터베이스에 저장
        await db.commit()
        
        return assignments

    @staticmethod
    async def set_ai_type(db: AsyncSession, room_code: str, ai_type: int):
        room = await RoomService.get_room_by_code(db, room_code)
        if not room:
            raise ValueError("존재하지 않는 방입니다.")
        if room.ai_type is not None:
            raise ValueError("이미 AI 형태가 저장되어 있습니다.")
        room.ai_type = ai_type
        await db.commit()
        return room

    @staticmethod
    async def get_ai_type(db: AsyncSession, room_code: str):
        room = await RoomService.get_room_by_code(db, room_code)
        if not room:
            raise ValueError("존재하지 않는 방입니다.")
        if room.ai_type is None:
            raise ValueError("아직 AI 형태가 저장되지 않았습니다.")
        return room.ai_type

    @staticmethod
    async def set_ai_name(db: AsyncSession, room_code: str, ai_name: str):
        room = await RoomService.get_room_by_code(db, room_code)
        if not room:
            raise ValueError("존재하지 않는 방입니다.")
        if room.ai_name:
            raise ValueError("이미 AI 이름이 저장되어 있습니다.")
        room.ai_name = ai_name
        await db.commit()
        return room

    @staticmethod
    async def get_ai_name(db: AsyncSession, room_code: str):
        room = await RoomService.get_room_by_code(db, room_code)
        if not room:
            raise ValueError("존재하지 않는 방입니다.")
        if not room.ai_name:
            raise ValueError("아직 AI 이름이 저장되지 않았습니다.")
        return room.ai_name

    @staticmethod
    async def submit_round_choice(
        db: AsyncSession,
        room_code: str,
        round_number: int,
        choice: int,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> models.RoundChoice:
        """라운드 개인 선택 제출"""
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        # 참가자 조회
        participant_query = select(models.RoomParticipant).where(
            and_(
                models.RoomParticipant.room_id == room.id,
                models.RoomParticipant.user_id == user_id if user_id else 
                models.RoomParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")
        
        # 합의 선택이 이미 완료되었는지 확인
        consensus_query = select(models.ConsensusChoice).where(
            and_(
                models.ConsensusChoice.room_id == room.id,
                models.ConsensusChoice.round_number == round_number
            )
        )
        consensus_result = await db.execute(consensus_query)
        consensus_choice = consensus_result.scalar_one_or_none()
        
        if consensus_choice:
            raise ValueError("합의 선택이 이미 완료되어 개인 선택을 변경할 수 없습니다.")
        
        # 기존 선택이 있는지 확인
        existing_choice_query = select(models.RoundChoice).where(
            and_(
                models.RoundChoice.room_id == room.id,
                models.RoundChoice.round_number == round_number,
                models.RoundChoice.participant_id == participant.id
            )
        )
        existing_choice_result = await db.execute(existing_choice_query)
        existing_choice = existing_choice_result.scalar_one_or_none()
        
        if existing_choice:
            # 기존 선택 업데이트
            existing_choice.choice = choice
            await db.commit()
            await db.refresh(existing_choice)
            return existing_choice
        else:
            # 새로운 선택 생성
            round_choice = models.RoundChoice(
                room_id=room.id,
                round_number=round_number,
                participant_id=participant.id,
                choice=choice
            )
            db.add(round_choice)
            await db.commit()
            await db.refresh(round_choice)
            return round_choice

    @staticmethod
    async def submit_individual_confidence(
        db: AsyncSession,
        room_code: str,
        round_number: int,
        confidence: int,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> models.RoundChoice:
        """개별 확신도 제출"""
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        # 참가자 조회
        participant_query = select(models.RoomParticipant).where(
            and_(
                models.RoomParticipant.room_id == room.id,
                models.RoomParticipant.user_id == user_id if user_id else 
                models.RoomParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")
        
        # 개인 선택이 있는지 확인
        choice_query = select(models.RoundChoice).where(
            and_(
                models.RoundChoice.room_id == room.id,
                models.RoundChoice.round_number == round_number,
                models.RoundChoice.participant_id == participant.id
            )
        )
        choice_result = await db.execute(choice_query)
        round_choice = choice_result.scalar_one_or_none()
        
        if not round_choice:
            raise ValueError("먼저 개인 선택을 제출해야 합니다.")
        
        # 확신도 업데이트
        round_choice.confidence = confidence
        await db.commit()
        await db.refresh(round_choice)
        return round_choice

    @staticmethod
    async def submit_consensus_choice(
        db: AsyncSession,
        room_code: str,
        round_number: int,
        choice: int,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> models.ConsensusChoice:
        """합의 선택 제출 (방장만 가능)"""
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        # 참가자 조회
        participant_query = select(models.RoomParticipant).where(
            and_(
                models.RoomParticipant.room_id == room.id,
                models.RoomParticipant.user_id == user_id if user_id else 
                models.RoomParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")
        
        # 방장인지 확인
        if not participant.is_host:
            raise ValueError("합의 선택은 방장만 제출할 수 있습니다.")
        
        # 모든 참가자가 개인 선택을 완료했는지 확인
        all_participants_query = select(models.RoomParticipant).where(
            models.RoomParticipant.room_id == room.id
        )
        all_participants_result = await db.execute(all_participants_query)
        all_participants = all_participants_result.scalars().all()
        
        for p in all_participants:
            choice_query = select(models.RoundChoice).where(
                and_(
                    models.RoundChoice.room_id == room.id,
                    models.RoundChoice.round_number == round_number,
                    models.RoundChoice.participant_id == p.id
                )
            )
            choice_result = await db.execute(choice_query)
            if not choice_result.scalar_one_or_none():
                raise ValueError("모든 참가자가 개인 선택을 완료해야 합니다.")
        
        # 기존 합의 선택이 있는지 확인
        existing_consensus_query = select(models.ConsensusChoice).where(
            and_(
                models.ConsensusChoice.room_id == room.id,
                models.ConsensusChoice.round_number == round_number
            )
        )
        existing_consensus_result = await db.execute(existing_consensus_query)
        existing_consensus = existing_consensus_result.scalar_one_or_none()
        
        if existing_consensus:
            # 기존 합의 선택 업데이트
            existing_consensus.choice = choice
            await db.commit()
            await db.refresh(existing_consensus)
            return existing_consensus
        else:
            # 새로운 합의 선택 생성
            consensus_choice = models.ConsensusChoice(
                room_id=room.id,
                round_number=round_number,
                choice=choice
            )
            db.add(consensus_choice)
            await db.commit()
            await db.refresh(consensus_choice)
            return consensus_choice

    @staticmethod
    async def submit_consensus_confidence(
        db: AsyncSession,
        room_code: str,
        round_number: int,
        confidence: int,
        user_id: Optional[int],
        guest_id: Optional[str]
    ) -> models.ConsensusChoice:
        """합의 선택에 대한 확신도 제출"""
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        # 참가자 조회
        participant_query = select(models.RoomParticipant).where(
            and_(
                models.RoomParticipant.room_id == room.id,
                models.RoomParticipant.user_id == user_id if user_id else 
                models.RoomParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        participant = result.scalar_one_or_none()
        
        if not participant:
            raise ValueError("방에 참가하지 않은 사용자입니다.")
        
        # 합의 선택이 있는지 확인
        consensus_query = select(models.ConsensusChoice).where(
            and_(
                models.ConsensusChoice.room_id == room.id,
                models.ConsensusChoice.round_number == round_number
            )
        )
        consensus_result = await db.execute(consensus_query)
        consensus_choice = consensus_result.scalar_one_or_none()
        
        if not consensus_choice:
            raise ValueError("먼저 합의 선택이 제출되어야 합니다.")
        
        # 확신도 업데이트
        consensus_choice.confidence = confidence
        await db.commit()
        await db.refresh(consensus_choice)
        return consensus_choice

    @staticmethod
    async def get_choice_status(
        db: AsyncSession,
        room_code: str,
        round_number: int
    ) -> schemas.ChoiceStatusResponse:
        """라운드별 선택 상태 조회"""
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        # 모든 참가자 조회
        participants_query = select(models.RoomParticipant).where(
            models.RoomParticipant.room_id == room.id
        )
        participants_result = await db.execute(participants_query)
        participants = participants_result.scalars().all()
        
        # 참가자별 선택 현황
        participant_status = []
        all_completed = True
        
        for participant in participants:
            # 개인 선택 조회
            choice_query = select(models.RoundChoice).where(
                and_(
                    models.RoundChoice.room_id == room.id,
                    models.RoundChoice.round_number == round_number,
                    models.RoundChoice.participant_id == participant.id
                )
            )
            choice_result = await db.execute(choice_query)
            round_choice = choice_result.scalar_one_or_none()
            
            status = {
                "participant_id": participant.id,
                "nickname": participant.nickname,
                "choice_completed": round_choice is not None,
                "choice": round_choice.choice if round_choice else None,
                "confidence_completed": round_choice.confidence is not None if round_choice else False,
                "confidence": round_choice.confidence if round_choice else None
            }
            participant_status.append(status)
            
            if not round_choice:
                all_completed = False
        
        # 합의 선택 조회
        consensus_query = select(models.ConsensusChoice).where(
            and_(
                models.ConsensusChoice.room_id == room.id,
                models.ConsensusChoice.round_number == round_number
            )
        )
        consensus_result = await db.execute(consensus_query)
        consensus_choice = consensus_result.scalar_one_or_none()
        
        consensus_completed = consensus_choice is not None
        can_proceed = all_completed and consensus_completed
        
        return schemas.ChoiceStatusResponse(
            round_number=round_number,
            room_code=room_code,
            participants=participant_status,
            all_completed=all_completed,
            consensus_completed=consensus_completed,
            can_proceed=can_proceed,
            consensus_choice=consensus_choice.choice if consensus_choice else None
        ) 

    @staticmethod
    async def get_role_assignment_status(
        db: AsyncSession,
        room_code: str
    ) -> schemas.RoleAssignmentStatus:
        """방의 역할 배정 상태 조회"""
        
        # 방 조회
        room = await RoomService.get_room_by_code(db=db, room_code=room_code)
        if not room:
            raise ValueError("존재하지 않는 방 코드입니다.")
        
        if not room.is_active:
            raise ValueError("비활성화된 방입니다.")
        
        # 방의 모든 참가자 조회
        participants_query = select(models.RoomParticipant).where(
            models.RoomParticipant.room_id == room.id
        )
        participants_result = await db.execute(participants_query)
        participants = participants_result.scalars().all()
        
        # 역할 배정 상태 확인
        assignments = []
        all_assigned = True
        
        for participant in participants:
            # 플레이어 ID 결정 (user_id 또는 guest_id)
            player_id = str(participant.user_id) if participant.user_id else participant.guest_id
            
            if participant.role_id is not None:
                # 역할이 배정된 경우
                assignment = schemas.RoleAssignment(
                    player_id=player_id,
                    role_id=participant.role_id,
                    role_name=schemas.ROLE_DEFINITIONS[participant.role_id]
                )
                assignments.append(assignment)
            else:
                # 역할이 배정되지 않은 경우
                all_assigned = False
        
        return schemas.RoleAssignmentStatus(
            room_code=room_code,
            is_roles_assigned=all_assigned and len(participants) == 3,
            assignments=assignments if all_assigned else [],
            total_participants=len(participants),
            assigned_participants=len([p for p in participants if p.role_id is not None])
        )

    @staticmethod
    async def get_room_participant_by_code(
        db: AsyncSession,
        room_code: str,
        user_id: Optional[int] = None,
        guest_id: Optional[str] = None
    ) -> Optional[models.RoomParticipant]:
        """room_code와 user_id/guest_id로 RoomParticipant 조회"""
        room = await RoomService.get_room_by_code(db, room_code)
        if not room:
            return None
        participant_query = select(models.RoomParticipant).where(
            and_(
                models.RoomParticipant.room_id == room.id,
                models.RoomParticipant.user_id == user_id if user_id else models.RoomParticipant.guest_id == guest_id
            )
        )
        result = await db.execute(participant_query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_room_participant_by_room_id(
        db: AsyncSession,
        room_id: int,
        user_id: Optional[int] = None,
        guest_id: Optional[str] = None
    ) -> Optional[models.RoomParticipant]:
        """room_id와 user_id/guest_id로 RoomParticipant 조회"""
        participant_query = None
        if user_id is not None:
            participant_query = select(models.RoomParticipant).where(
                models.RoomParticipant.room_id == room_id,
                models.RoomParticipant.user_id == user_id
            )
        elif guest_id is not None:
            participant_query = select(models.RoomParticipant).where(
                models.RoomParticipant.room_id == room_id,
                models.RoomParticipant.guest_id == guest_id
            )
        else:
            return None
        result = await db.execute(participant_query)
        return result.scalar_one_or_none()


# 서비스 인스턴스
room_service = RoomService() 