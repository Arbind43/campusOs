# Re-export from the unified campus schemas for backwards compatibility.
from app.schemas.campus import SyncProfileRequest, UserProfileOut

__all__ = ["SyncProfileRequest", "UserProfileOut"]
