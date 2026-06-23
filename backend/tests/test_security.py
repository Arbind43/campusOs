from unittest.mock import MagicMock, patch

from app.core.security import verify_supabase_token


def test_verify_supabase_token_uses_jwks_for_es256_tokens():
    signing_key = MagicMock()
    signing_key.key = "public-key"

    jwks_client = MagicMock()
    jwks_client.get_signing_key_from_jwt.return_value = signing_key

    expected_payload = {"sub": "user-id", "aud": "authenticated"}

    with patch("app.core.security.jwt.get_unverified_header", return_value={"alg": "ES256"}):
        with patch("app.core.security._get_jwks_client", return_value=jwks_client):
            with patch("app.core.security.jwt.decode", return_value=expected_payload) as decode:
                payload = verify_supabase_token("token")

    assert payload == expected_payload
    jwks_client.get_signing_key_from_jwt.assert_called_once_with("token")
    decode.assert_called_once()
    _, key = decode.call_args.args[:2]
    assert key == "public-key"
    assert decode.call_args.kwargs["algorithms"] == ["ES256"]
