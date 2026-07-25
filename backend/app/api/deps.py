"""Shared FastAPI dependencies: current user resolution & role guards."""
from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

_CREDS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _user_from_token(token: str, db: Session) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise _CREDS_EXC
    user = db.query(User).filter(User.email == payload["sub"]).first()
    if user is None:
        raise _CREDS_EXC
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    return _user_from_token(token, db)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin/police access required")
    return user


def require_self_or_admin(
    tourist_id: int = Path(...), user: User = Depends(get_current_user)
) -> User:
    """Allow admins, or a tourist acting only on their own record."""
    if user.role == "admin":
        return user
    if user.role == "tourist" and user.tourist_id == tourist_id:
        return user
    raise HTTPException(status_code=403, detail="Forbidden")


def authenticate_ws_token(token: str | None, db: Session) -> User | None:
    """Validate a token passed as a WebSocket query param. Returns None if invalid."""
    if not token:
        return None
    try:
        return _user_from_token(token, db)
    except HTTPException:
        return None
