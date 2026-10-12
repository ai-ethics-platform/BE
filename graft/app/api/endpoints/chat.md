# app/api/endpoints/chat.py

- chat_with_prompt · function · L17-L67 — async def chat_with_prompt(payload: ChatRequest, db: AsyncSession = Depends(get_db)) -> Any
- generate_image · function · L71-L194 — async def generate_image(payload: ImageRequest) -> Any
- multi_step_chat · function · L198-L217 — async def multi_step_chat( request: MultiStepChatRequest, db: AsyncSession = Depends(get_db) ) -> Any
- get_session_info · function · L221-L233 — async def get_session_info(session_id: str, db: AsyncSession = Depends(get_db)) -> Any
- delete_session · function · L237-L250 — async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)) -> Any
