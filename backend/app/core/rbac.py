from fastapi import Depends, HTTPException, status
from app.models.user import User, Role
from app.api.deps import get_current_user

ROLE_ORDER = {Role.VIEWER: 0, Role.ANALYST: 1, Role.ADMIN: 2}

def require_role(minimum_role: Role):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_ORDER[current_user.role] < ROLE_ORDER[minimum_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return dependency
