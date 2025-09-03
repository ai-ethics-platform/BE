from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil

from app.core.deps import get_db
from app.core.config import settings
from app import schemas
from app.services.custom_game_service import custom_game_service
from app import models
import smtplib
from email.mime.text import MIMEText


router = APIRouter()


@router.post("/custom-games", response_model=schemas.CustomGameCreateResponse)
async def create_custom_game(
    payload: schemas.CustomGameCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.create(
        db=db,
        teacher_name=payload.teacher_name,
        teacher_school=payload.teacher_school,
        teacher_email=payload.teacher_email,
        title=payload.title,
        representative_image_url=payload.representative_image_url,
        data=payload.data,
    )
    base_url = os.getenv("FRONTEND_BASE_URL", "https://dilemmai.org")
    return {"code": game.code, "url": f"{base_url}/game/{game.code}"}


@router.get("/custom-games/{code}", response_model=schemas.CustomGame)
async def get_custom_game(code: str, db: AsyncSession = Depends(get_db)) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="커스텀 게임을 찾을 수 없습니다.")
    # Convert JSON string to dict for response schema
    import json
    game.data = json.loads(game.data) if isinstance(game.data, str) else game.data
    return game


# Representative image upload
IMAGE_DIR = "static/images"
os.makedirs(IMAGE_DIR, exist_ok=True)


@router.post("/custom-games/upload-image")
async def upload_representative_image(
    file: UploadFile = File(...)
) -> Any:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="JPG 또는 PNG 파일만 허용됩니다.")
    filename = f"cg_{os.urandom(8).hex()}{ext}"
    path = os.path.join(IMAGE_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    url_path = f"/static/images/{filename}"
    return {"url": url_path}


@router.post("/custom-games/{code}/send-email")
async def send_custom_game_email(code: str, to_email: str = Form(...)) -> Any:
    frontend_base = os.getenv("FRONTEND_BASE_URL", "https://dilemmai.org")
    game_url = f"{frontend_base}/game/{code}"
    subject = "딜레마 게임 링크"
    body = f"안녕하세요, 요청하신 커스텀 딜레마 게임 링크입니다: {game_url}"

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "noreply@example.com")

    if not smtp_host or not smtp_user or not smtp_pass:
        raise HTTPException(status_code=400, detail="SMTP 설정이 누락되었습니다.")

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_from, [to_email], msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이메일 전송 실패: {str(e)}")

    return {"message": "이메일이 전송되었습니다.", "to": to_email, "url": game_url}



