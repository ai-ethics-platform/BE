# app/services/admin_play_application_service.py

- get_all_applications · function · L10-L36 — async def get_all_applications( db: AsyncSession, status_filter: Optional[str] = None, ) -> List[models.PlayApplication]
- get_application_by_id · function · L39-L52 — async def get_application_by_id( db: AsyncSession, application_id: int, ) -> Optional[models.PlayApplication]
- approve_application · function · L55-L86 — async def approve_application( db: AsyncSession, application_id: int, ) -> models.PlayApplication
- reject_application · function · L89-L120 — async def reject_application( db: AsyncSession, application_id: int, ) -> models.PlayApplication
- cancel_approval · function · L123-L154 — async def cancel_approval( db: AsyncSession, application_id: int, ) -> models.PlayApplication
- delete_rejected_applications · function · L157-L176 — async def delete_rejected_applications( db: AsyncSession, ) -> int
