"""API router for the Identity module."""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserIdDep
from app.core.exceptions import UnauthorizedError
from app.modules.identity.api.dependencies import AuthServiceDep, UserRepoDep
from app.modules.identity.application.services import IdentityService
from app.modules.identity.schemas.auth_schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(data: RegisterRequest, auth_service: AuthServiceDep) -> UserResponse:
    """Register a new user account."""
    user = await auth_service.register(data)
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get tokens",
)
async def login(data: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    """Authenticate a user and return access/refresh tokens."""
    user = await auth_service.login(data)
    access_token = IdentityService.create_access_token(user.id)
    refresh_token = IdentityService.create_refresh_token(user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        # Default in config is 15 minutes, but let's just return a placeholder or 
        # actual config value. We'll return 900 (15 min) for now.
        expires_in=900,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(data: RefreshRequest) -> TokenResponse:
    """Get a new access token using a refresh token."""
    user_id = await IdentityService.verify_refresh_token(data.refresh_token)
    
    access_token = IdentityService.create_access_token(user_id)
    new_refresh_token = IdentityService.create_refresh_token(user_id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=900,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
)
async def get_current_user(user_id: CurrentUserIdDep, user_repo: UserRepoDep) -> UserResponse:
    """Get the profile of the currently authenticated user."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedError("User no longer exists")
        
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
    )
