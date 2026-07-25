from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.ratelimit import login_rate_limit
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserOut
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token, dependencies=[Depends(login_rate_limit)])
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    """OAuth2 password flow — `username` field carries the email."""
    user = db.query(User).filter(User.email == form.username).first()
    # Constant-ish response: same error whether the email exists or not.
    if not user or not verify_password(form.password, user.hashed_password):
        audit.record(db, "login", actor=form.username or "unknown",
                     outcome="failure", request=request, detail="bad credentials")
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    audit.record(db, "login", actor=user.email, outcome="success", request=request)
    token = create_access_token(subject=user.email, role=user.role, tourist_id=user.tourist_id)
    return Token(
        access_token=token, role=user.role,
        tourist_id=user.tourist_id, full_name=user.full_name,
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
