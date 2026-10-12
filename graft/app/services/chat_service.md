# app/services/chat_service.py

- ChatService · class · L16-L311 — class ChatService
- __init__ · method · L17-L61 — def __init__(self)
- get_or_create_session · method · L63-L80 — async def get_or_create_session(self, db: AsyncSession, session_id: str) -> ChatSession
- update_session · method · L82-L99 — async def update_session(self, db: AsyncSession, session_id: str, update_data: ChatSessionUpdate) -> ChatSession
- get_next_step · method · L101-L109 — def get_next_step(self, current_step: str) -> Optional[str]
- is_last_step · method · L111-L113 — def is_last_step(self, current_step: str) -> bool
- call_openai_response · method · L115-L257 — async def call_openai_response(self, step: str, user_input: str, context: Dict[str, Any], manual_variables: Optional[Dict[str, Any]] = None) -> tuple[str, Dict[str, Any]]
- process_multi_step_chat · method · L259-L311 — async def process_multi_step_chat( self, db: AsyncSession, request: MultiStepChatRequest ) -> MultiStepChatResponse
