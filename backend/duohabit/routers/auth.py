"""Auth endpoints."""

from fastapi import APIRouter

from duohabit.auth import login_router

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

auth_router.include_router(login_router)

# Left for potential session management.
