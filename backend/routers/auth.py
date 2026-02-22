"""
Auth Router
────────────
POST /auth/login   — returns JWT token
GET  /auth/me      — returns current user info
POST /auth/register
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import get_db
from config   import settings
from models.workflow import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context     = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme   = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      int
    name:         str
    role:         str


class RegisterIn(BaseModel):
    name:       str
    email:      EmailStr
    password:   str
    role:       UserRole = UserRole.FACULTY
    department: Optional[str] = None


class UserOut(BaseModel):
    id:         int
    name:       str
    email:      str
    role:       str
    department: Optional[str]
    is_active:  bool

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def _create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user   = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: RegisterIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = User(
        name=data.name,
        email=data.email,
        hashed_password=_hash_password(data.password),
        role=data.role,
        department=data.department,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db:   AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form.username))
    user   = result.scalar_one_or_none()
    if not user or not _verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    token = _create_token({"sub": str(user.id)})
    return Token(access_token=token, user_id=user.id, name=user.name, role=user.role.value)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
