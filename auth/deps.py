"""FastAPI dependencies for authentication and role-based access control.

These dependencies rely on ``request.state.user`` being populated by
``JWTAuthMiddleware`` before any route handler runs. They can be used
directly in route definitions via ``Depends()``.

Usage::

    from auth.deps import get_current_user, require_role
    from fastapi import APIRouter, Depends

    router = APIRouter()

    @router.get("/me")
    async def me(current_user: dict = Depends(get_current_user)):
        return current_user

    @router.get("/seller-only", dependencies=[Depends(require_role("seller"))])
    async def seller_only():
        return {"ok": True}
"""

from __future__ import annotations

from fastapi import Request

# ---------------------------------------------------------------------------
# Public dependencies
# ---------------------------------------------------------------------------


def get_current_user(request: Request) -> dict[str, str]:
    """Return the authenticated user dict injected by the JWT middleware.

    This dependency expects ``JWTAuthMiddleware`` to have already validated
    the token and populated ``request.state.user`` with::

        {"user_id": str, "role": str, "email": str}

    Raises:
        HTTPException(401): If ``request.state.user`` has not been set
            (i.e. the middleware did not run or authentication failed).
    """
    from fastapi import HTTPException

    user: dict[str, str] | None = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )
    return user


def require_role(*roles: str):
    """Return a dependency that enforces the current user has one of *roles*.

    The returned callable inspects ``request.state.user["role"]`` and raises
    ``HTTPException(403)`` if the role does not match any of the allowed values.

    Example::

        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_dashboard():
            ...

        @router.get("/staff", dependencies=[Depends(require_role("admin", "moderator"))])
        async def staff_tools():
            ...
    """
    from fastapi import HTTPException

    allowed_roles = set(roles)

    def role_checker(request: Request) -> None:
        user: dict[str, str] | None = getattr(request.state, "user", None)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
            )
        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {', '.join(sorted(allowed_roles))}",
            )

    return role_checker
