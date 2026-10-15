
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from backend.app.models.user import User
from backend.app.schemas.auth import UserLogin, UserRegister
from backend.app.services.auth_audit_service import record_auth_event


def register_user(db: Session, request: UserRegister) -> User:
    """Register a new OPERATOR account and record the audit event."""
    email = str(request.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        password_hash=hash_password(request.password),
        role="OPERATOR",
    )

    try:
        db.add(user)
        db.flush()

        record_auth_event(
            db=db,
            action="USER_REGISTERED",
            user_id=user.id,
        )

        db.commit()
        db.refresh(user)
        return user

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc

    except Exception:
        db.rollback()
        raise


def authenticate_user(db: Session, request: UserLogin) -> dict:
    """Validate credentials, record the login event, and issue a JWT."""
    email = str(request.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        record_auth_event(
            db=db,
            action="USER_LOGIN",
            user_id=user.id,
        )

        db.commit()

        token = create_access_token(
            user_id=UUID(str(user.id)),
            role=user.role,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user,
        }

    except Exception:
        db.rollback()
        raise
