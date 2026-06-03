import pytest
from datetime import timedelta

def test_hash_and_verify_password():
    from app.core.security import hash_password, verify_password
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert verify_password("mysecret", hashed)
    assert not verify_password("wrong", hashed)

def test_create_and_decode_token():
    from app.core.security import create_access_token, decode_access_token
    import uuid
    user_id = uuid.uuid4()
    token = create_access_token(str(user_id), "analyst")
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "analyst"

def test_expired_token_raises():
    from app.core.security import create_access_token, decode_access_token
    from jose import JWTError
    import uuid
    token = create_access_token(str(uuid.uuid4()), "viewer", expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_access_token(token)
