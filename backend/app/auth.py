from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User


bearer = HTTPBearer()


def create_access_token(user: User) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user.id), "email": user.email, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_or_create_user(db: Session, *, email: str, name: str, provider: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, name=name, provider=provider)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
