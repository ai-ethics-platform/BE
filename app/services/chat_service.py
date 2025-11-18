from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import OpenAI
from pydantic import BaseModel
import os
import uuid
import json

from app.core.config import settings
from app.models.chat_session import ChatSession
from app.schemas.chat_session import ChatSessionCreate, ChatSessionUpdate, MultiStepChatRequest, MultiStepChatResponse
from app.schemas.step_responses import STEP_RESPONSE_MODELS


class ChatService:
    def __init__(self):
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # 단계별 순서 정의
        self.step_order = ["opening", "dilemma", "flip", "roles", "ending"]
    
    async def get_or_create_session(self, db: AsyncSession, session_id: str) -> ChatSession:
        """세션을 가져오거나 새로 생성"""
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            session = ChatSession(
                session_id=session_id,
                current_step="opening",
                context={}
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        
        return session
    
    async def update_session(self, db: AsyncSession, session_id: str, update_data: ChatSessionUpdate) -> ChatSession:
        """세션 업데이트"""
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if update_data.current_step:
            session.current_step = update_data.current_step
        if update_data.context is not None:
            session.context = update_data.context
        
        await db.commit()
        await db.refresh(session)
        return session
    
    def get_next_step(self, current_step: str) -> Optional[str]:
        """다음 단계 반환"""
        try:
            current_index = self.step_order.index(current_step)
            if current_index < len(self.step_order) - 1:
                return self.step_order[current_index + 1]
            return None
        except ValueError:
            return None
    
    def is_last_step(self, current_step: str) -> bool:
        """마지막 단계인지 확인"""
        return current_step == self.step_order[-1]
    
    async def call_openai_response(self, step: str, user_input: str, context: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        OpenAI Responses API 호출 후 LangChain으로 JSON 파싱
        
        Returns:
            tuple[str, Dict[str, Any]]: (response_text, parsed_variables)
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        # 단계별 프롬프트 정보 가져오기
        prompt_config = settings.CHATBOT_PROMPTS.get(step)
        if not prompt_config:
            raise ValueError(f"No prompt configuration found for step: {step}")
        
        # input_variables 구성 (이전 단계 결과들 + 현재 사용자 입력)
        input_variables = context.copy()
        input_variables["user_input"] = user_input
        
        try:
            # 1. OpenAI Playground API로 프롬프트 처리
            prompt_obj = {
                "id": prompt_config["id"],
                "version": prompt_config["version"]
            }
            
            # variables가 있으면 prompt 객체 안에 포함
            if input_variables:
                prompt_obj["variables"] = input_variables
            
            response = self.openai_client.responses.create(
                prompt=prompt_obj,
                input=user_input
            )
            
            # 응답 텍스트 추출
            text_parts = []
            for item in getattr(response, "output", []) or []:
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") == "output_text":
                        text_parts.append(getattr(c, "text", ""))
            
            raw_response_text = "".join(text_parts).strip()
            
            # 2. LangChain으로 JSON 파싱 시도
            parsed_variables = {}
            try:
                from langchain_openai import ChatOpenAI
                from langchain.prompts import ChatPromptTemplate
                from langchain.schema.output_parser import PydanticOutputParser
                
                # 단계별 응답 모델 가져오기
                response_model = STEP_RESPONSE_MODELS.get(step)
                if response_model:
                    llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=0.7,
                        api_key=settings.OPENAI_API_KEY,
                    )
                    
                    # PydanticOutputParser 생성
                    parser = PydanticOutputParser(pydantic_object=response_model)
                    
                    # JSON 형식으로 출력하도록 지시하는 프롬프트
                    format_instructions = parser.get_format_instructions()
                    
                    prompt_template = ChatPromptTemplate.from_template(
                        """다음 응답을 JSON 형식으로 변환해주세요. 
응답 텍스트: {raw_response}

{format_instructions}

원본 응답의 내용을 유지하면서, 위 JSON 스키마에 맞춰서 구조화해주세요.
response_text 필드에는 사용자에게 보여줄 원본 응답 텍스트를 넣어주세요."""
                    )
                    
                    # 체인 실행
                    chain = prompt_template | llm | parser
                    parsed_result = await chain.ainvoke({
                        "raw_response": raw_response_text,
                        "format_instructions": format_instructions
                    })
                    
                    # 파싱된 결과에서 변수 추출
                    if isinstance(parsed_result, BaseModel):
                        parsed_dict = parsed_result.model_dump()
                        # response_text는 제외하고 나머지를 variables로
                        parsed_variables = {k: v for k, v in parsed_dict.items() if k != "response_text"}
                        # response_text가 있으면 그것을 사용
                        if "response_text" in parsed_dict and parsed_dict["response_text"]:
                            raw_response_text = parsed_dict["response_text"]
                    
            except Exception as parse_error:
                # JSON 파싱 실패 시 원본 텍스트 사용
                # 로깅할 수 있지만 에러를 발생시키지는 않음
                pass
            
            return raw_response_text, parsed_variables
            
        except Exception as e:
            raise ValueError(f"OpenAI API call failed: {e}")
    
    async def process_multi_step_chat(
        self, 
        db: AsyncSession, 
        request: MultiStepChatRequest
    ) -> MultiStepChatResponse:
        """다단계 챗봇 처리"""
        # 세션 가져오기 또는 생성
        session = await self.get_or_create_session(db, request.session_id)
        
        # 실행할 단계 결정
        current_step = request.step or session.current_step
        
        # OpenAI API 호출 (JSON 파싱 포함)
        response_text, parsed_variables = await self.call_openai_response(
            current_step, 
            request.user_input, 
            session.context or {}
        )
        
        # 컨텍스트 업데이트 (현재 단계 결과 저장)
        updated_context = session.context.copy() if session.context else {}
        updated_context[f"{current_step}_result"] = response_text
        updated_context[f"{current_step}_user_input"] = request.user_input
        
        # 파싱된 변수들을 컨텍스트에 추가
        if parsed_variables:
            for key, value in parsed_variables.items():
                updated_context[f"{current_step}_{key}"] = value
        
        # 다음 단계 결정
        next_step = self.get_next_step(current_step)
        is_complete = self.is_last_step(current_step)
        
        # 세션 업데이트
        await self.update_session(
            db, 
            request.session_id,
            ChatSessionUpdate(
                current_step=next_step if next_step else current_step,
                context=updated_context
            )
        )
        
        return MultiStepChatResponse(
            session_id=request.session_id,
            current_step=current_step,
            response_text=response_text,
            parsed_variables=parsed_variables,
            context=updated_context,
            next_step=next_step,
            is_complete=is_complete
        )


# 전역 인스턴스
chat_service = ChatService()
