# app/api/endpoints/admin_play_applications.py

- handle_service_error · function · L14-L30 — def handle_service_error(exc: ValueError) -> None
- get_play_applications · function · L37-L79 — async def get_play_applications( status_filter: Optional[str] = Query( default=None, alias="status", description="pending, approved, rejected 중 하나", ), db: AsyncSession = Depends(get_db), current_admin: models.User = Depends(get_current_admin_user), ) -> Any
- approve_play_application · function · L86-L111 — async def approve_play_application( application_id: int, db: AsyncSession = Depends(get_db), current_admin: models.User = Depends(get_current_admin_user), ) -> Any
- reject_play_application · function · L118-L143 — async def reject_play_application( application_id: int, db: AsyncSession = Depends(get_db), current_admin: models.User = Depends(get_current_admin_user), ) -> Any
- cancel_play_application_approval · function · L150-L175 — async def cancel_play_application_approval( application_id: int, db: AsyncSession = Depends(get_db), current_admin: models.User = Depends(get_current_admin_user), ) -> Any
- delete_rejected_play_applications · function · L181-L197 — async def delete_rejected_play_applications( db: AsyncSession = Depends(get_db), current_admin: models.User = Depends(get_current_admin_user), ) -> Any
