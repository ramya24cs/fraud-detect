from uuid import uuid4

from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verification():
    password = "Test-Password-123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("Wrong-Password", hashed)


def test_access_token_round_trip():
    user_id = uuid4()

    token = create_access_token(
        user_id=user_id,
        role="OPERATOR",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "OPERATOR"