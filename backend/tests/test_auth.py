import uuid

import pytest
from fastapi import HTTPException

from app.auth import create_access_token, decode_access_token, hash_password, verify_password


def test_password_round_trip():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_round_trip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    assert decode_access_token(token) == user_id


def test_invalid_token_is_rejected():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-jwt")
    assert exc_info.value.status_code == 401
