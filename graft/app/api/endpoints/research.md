# app/api/endpoints/research.py

- research_dashboard · function · L39-L43 — async def research_dashboard()
- get_experiment_summary · function · L47-L83 — async def get_experiment_summary( db: AsyncSession = Depends(get_db) ) -> Any
- export_experiment_data · function · L87-L250 — async def export_experiment_data( started_only: bool = Query(True, description="완료된 게임만 포함"), with_consent_only: bool = Query(True, description="동의한 사용자만 포함"), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: AsyncSession = Depends(get_db) ) -> Any
- get_room_detail · function · L254-L386 — async def get_room_detail( room_id: int, db: AsyncSession = Depends(get_db) ) -> Any
- get_room_detail_by_code · function · L390-L527 — async def get_room_detail_by_code( room_code: str, db: AsyncSession = Depends(get_db) ) -> Any
- get_user_experiment_data · function · L531-L613 — async def get_user_experiment_data( user_id: int, db: AsyncSession = Depends(get_db) ) -> Any
- delete_test_data · function · L617-L716 — async def delete_test_data( request: DeleteTestDataRequest, db: AsyncSession = Depends(get_db) ) -> Any
- analyze_choices · function · L720-L799 — async def analyze_choices( topic: Optional[str] = None, db: AsyncSession = Depends(get_db) ) -> Any
- export_experiment_data_to_excel · function · L803-L981 — async def export_experiment_data_to_excel( started_only: bool = Query(False, description="시작된 게임만 포함"), with_consent_only: bool = Query(False, description="동의한 사용자만 포함"), topic: Optional[str] = Query(None, description="특정 주제 필터링"), db: AsyncSession = Depends(get_db) )
- _get_role_string · function · L984-L991 — def _get_role_string(role_id: Optional[int]) -> str
- get_data_counts · function · L995-L1044 — async def get_data_counts(db: AsyncSession = Depends(get_db))
- get_voice_recordings · function · L1048-L1165 — async def get_voice_recordings( room_code: Optional[str] = Query(None, description="방 코드로 필터링 (6자리)"), room_id: Optional[int] = Query(None, description="방 ID로 필터링"), creator_id: Optional[int] = Query(None, description="방장(생성자) ID로 필터링"), user_id: Optional[int] = Query(None, description="특정 사용자 ID로 필터링"), start_date: Optional[datetime] = Query(None, description="시작 날짜 (YYYY-MM-DD)"), end_date: Optional[datetime] = Query(None, description="종료 날짜 (YYYY-MM-DD)"), skip: int = Query(0, ge=0, description="페이지네이션 오프셋"), limit: int = Query(100, ge=1, le=500, description="가져올 개수"), db: AsyncSession = Depends(get_db) ) -> Any
