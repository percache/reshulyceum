from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas.user import PasswordChange, Token, UserCreate, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

AVATAR_DIR = Path("app/static/uploads/avatars")
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_AVATAR_SIZE = 2 * 1024 * 1024


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="User with this email or username already exists")
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if avatar.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(status_code=400, detail="Upload JPG, PNG or WEBP image")

    data = await avatar.read()
    if len(data) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Avatar must be smaller than 2 MB")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    ext = ALLOWED_AVATAR_TYPES[avatar.content_type]
    path = AVATAR_DIR / f"user_{current.id}{ext}"
    path.write_bytes(data)

    current.avatar_path = f"/static/uploads/avatars/{path.name}"
    db.add(current)
    db.commit()
    db.refresh(current)
    return current


@router.post("/me/password", response_model=UserOut)
def change_password(
    payload: PasswordChange,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, current.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is wrong")
    if payload.old_password == payload.new_password:
        raise HTTPException(status_code=400, detail="New password must differ")
    current.hashed_password = hash_password(payload.new_password)
    db.add(current)
    db.commit()
    db.refresh(current)
    return current
