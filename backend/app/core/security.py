"""
JWT token handling - SUPER SIMPLIFIED for development.
No actual JWT - just pass user ID directly.
"""
import uuid
from datetime import datetime, timedelta

import jwt


def create_simple_token(user_id: str, email: str) -> str:
    """Create a simple JWT token for development."""
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    # Simple secret - doesn't matter in dev
    return jwt.encode(payload, "dev-secret-key", algorithm="HS256")


def verify_simple_token(token: str) -> dict:
    """Decode token without verification (dev mode)."""
    try:
        return jwt.decode(token, "dev-secret-key", algorithms=["HS256"], options={"verify_exp": False})
    except:
        # Fallback: decode without verification
        return jwt.decode(token, options={"verify_signature": False, "verify_aud": False, "verify_exp": False})


# Keep old function name for compatibility
def verify_supabase_token(token: str) -> dict:
    """Decode JWT without verification (dev mode)."""
    return verify_simple_token(token)
