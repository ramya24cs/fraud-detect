from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from backend.app.services.auth_service import (
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    """Create a public OPERATOR account."""
    return register_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate credentials and issue a JWT."""
    result = authenticate_user(db, data)

    return TokenResponse(
        access_token=result["access_token"],
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/token", response_model=TokenResponse)
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2-compatible login using form-encoded credentials."""
    credentials = UserLogin(
        email=form_data.username,
        password=form_data.password,
    )
    result = authenticate_user(db, credentials)

    return TokenResponse(
        access_token=result["access_token"],
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )