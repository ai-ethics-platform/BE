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
    base_url = os.getenv("FRONTEND_BASE_URL", "https://www.dilemmai-idl.com")
    return {"code": game.code, "url": f"{base_url}/game/{game.code}"}


@router.get("/custom-games/{code}", response_model=schemas.CustomGame)
async def get_custom_game(code: str, db: AsyncSession = Depends(get_db)) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="커스텀 게임을 찾을 수 없습니다.")
    # Convert JSON string to dict for response schema
    import json
    game.data = json.loads(game.data) if isinstance(game.data, str) else game.data
    # expose representative_images from data if present
    rep_images = game.data.get("representativeImages") if isinstance(game.data, dict) else None
    if rep_images:
        game.representative_images = rep_images
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


# Representative images mapping (multiple named images)
@router.put("/custom-games/{code}/representative-images")
async def update_representative_images(
    code: str,
    payload: schemas.RepresentativeImagesUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    await _merge_and_save(db, game, {"representativeImages": payload.images})
    return {"message": "updated"}


@router.get("/custom-games/{code}/representative-images", response_model=schemas.RepresentativeImagesResponse)
async def get_representative_images(code: str, db: AsyncSession = Depends(get_db)) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    data = _load_data(game)
    images = data.get("representativeImages", {})
    return {"images": images}


# --- Sectional updates ---
def _load_data(game) -> dict:
    import json
    return json.loads(game.data) if isinstance(game.data, str) else (game.data or {})


async def _merge_and_save(db: AsyncSession, game, patch: dict) -> None:
    import json
    data = _load_data(game)
    data.update(patch)
    game.data = json.dumps(data, ensure_ascii=False)
    await db.commit()
    await db.refresh(game)


@router.put("/custom-games/{code}/opening")
async def update_opening(
    code: str,
    payload: schemas.OpeningUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    await _merge_and_save(db, game, {"opening": payload.opening})
    return {"message": "updated"}


@router.put("/custom-games/{code}/roles")
async def update_roles(
    code: str,
    payload: schemas.RolesUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    patch = {"roles": [r.model_dump() for r in payload.roles]}
    if payload.background is not None:
        patch["rolesBackground"] = payload.background
    await _merge_and_save(db, game, patch)
    return {"message": "updated"}


@router.put("/custom-games/{code}/dilemma")
async def update_dilemma(
    code: str,
    payload: schemas.DilemmaUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    await _merge_and_save(db, game, {
        "dilemma": {
            "situation": payload.situation,
            "question": payload.question,
            "options": payload.options.model_dump()
        }
    })
    return {"message": "updated"}


@router.put("/custom-games/{code}/flips")
async def update_flips(
    code: str,
    payload: schemas.FlipsUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    await _merge_and_save(db, game, {
        "flips": {
            "agree_texts": payload.agree_texts,
            "disagree_texts": payload.disagree_texts
        }
    })
    return {"message": "updated"}


@router.put("/custom-games/{code}/ending")
async def update_ending(
    code: str,
    payload: schemas.EndingUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    await _merge_and_save(db, game, {
        "finalMessages": {
            "agree": payload.agree,
            "disagree": payload.disagree
        }
    })
    return {"message": "updated"}


# Title endpoints
@router.put("/custom-games/{code}/title")
async def update_title(
    code: str,
    payload: schemas.TitleUpdate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    # db column에도 반영
    game.title = payload.title
    await _merge_and_save(db, game, {"title": payload.title})
    return {"message": "updated"}


@router.get("/custom-games/{code}/title", response_model=schemas.TitleResponse)
async def get_title(code: str, db: AsyncSession = Depends(get_db)) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    return {"title": game.title}


# Roles GET
@router.get("/custom-games/{code}/roles", response_model=schemas.RolesResponse)
async def get_roles(code: str, db: AsyncSession = Depends(get_db)) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    data = _load_data(game)
    roles = data.get("roles", [])
    background = data.get("rolesBackground")
    return {"roles": roles, "background": background}


# Per-slot role image upload and list
ROLE_IMAGE_DIR = os.path.join(IMAGE_DIR, "roles")
os.makedirs(ROLE_IMAGE_DIR, exist_ok=True)


@router.post("/custom-games/{code}/role-images/{slot}")
async def upload_role_image(
    code: str,
    slot: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> Any:
    if slot not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="slot은 1,2,3만 허용됩니다.")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="JPG 또는 PNG 파일만 허용됩니다.")
    filename = f"cg_role_{slot}_{os.urandom(8).hex()}{ext}"
    path = os.path.join(ROLE_IMAGE_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    url_path = f"/static/images/roles/{filename}"
    # store into game.data.roleImages[slot]
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    current = _load_data(game).get("roleImages", {})
    current[str(slot)] = url_path
    await _merge_and_save(db, game, {"roleImages": current})
    return {"url": url_path}


@router.get("/custom-games/{code}/role-images", response_model=schemas.RoleImagesResponse)
async def get_role_images(code: str, db: AsyncSession = Depends(get_db)) -> Any:
    game = await custom_game_service.get_by_code(db, code)
    if not game:
        raise HTTPException(status_code=404, detail="커스텀 게임을 찾을 수 없습니다.")
    data = _load_data(game)
    urls = data.get("roleImages", {})
    return {"urls": urls}


@router.post("/custom-games/{code}/send-email")
async def send_custom_game_email(code: str, to_email: str = Form(...)) -> Any:
    frontend_base = os.getenv("FRONTEND_BASE_URL", "https://www.dilemmai-idl.com")
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



