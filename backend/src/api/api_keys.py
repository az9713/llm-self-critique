"""API Key management endpoints."""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.analytics import APIKey, APIKeyStatus


router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


class APIKeyCreate(BaseModel):
    """Request model for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100, description="Name for the API key")
    rate_limit: int = Field(default=100, ge=1, le=10000, description="Requests per minute")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration date")


class APIKeyResponse(BaseModel):
    """Response model for API key (without the actual key)."""
    id: UUID
    name: str
    key_prefix: str
    status: str
    rate_limit: int
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]


class APIKeyCreatedResponse(BaseModel):
    """Response model when creating an API key (includes the actual key)."""
    id: UUID
    name: str
    key: str  # Only returned on creation
    key_prefix: str
    status: str
    rate_limit: int
    created_at: datetime
    expires_at: Optional[datetime]
    warning: str = "Store this key securely. It will not be shown again."


class APIKeyUpdate(BaseModel):
    """Request model for updating an API key."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    status: Optional[str] = Field(None, description="'active' or 'revoked'")


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        tuple of (raw_key, key_hash, key_prefix)
    """
    # Generate a secure random key
    raw_key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]
    return raw_key, key_hash, key_prefix


@router.post("", response_model=APIKeyCreatedResponse)
async def create_api_key(
    request: APIKeyCreate,
    user_id: UUID = Query(..., description="User ID for the API key"),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreatedResponse:
    """
    Create a new API key.

    The raw key is only returned once on creation. Store it securely.
    """
    raw_key, key_hash, key_prefix = generate_api_key()

    api_key = APIKey(
        user_id=user_id,
        name=request.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        rate_limit=request.rate_limit,
        expires_at=request.expires_at,
    )

    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return APIKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key=raw_key,
        key_prefix=api_key.key_prefix,
        status=api_key.status.value,
        rate_limit=api_key.rate_limit,
        created_at=api_key.created_at,
        expires_at=api_key.expires_at,
    )


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    user_id: UUID = Query(..., description="User ID to list keys for"),
    include_revoked: bool = Query(False, description="Include revoked keys"),
    db: AsyncSession = Depends(get_db),
) -> List[APIKeyResponse]:
    """List all API keys for a user."""
    filters = [APIKey.user_id == user_id]

    if not include_revoked:
        filters.append(APIKey.status == APIKeyStatus.ACTIVE)

    result = await db.execute(
        select(APIKey)
        .where(and_(*filters))
        .order_by(APIKey.created_at.desc())
    )
    keys = result.scalars().all()

    return [
        APIKeyResponse(
            id=key.id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status.value,
            rate_limit=key.rate_limit,
            created_at=key.created_at,
            last_used_at=key.last_used_at,
            expires_at=key.expires_at,
        )
        for key in keys
    ]


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: UUID,
    user_id: UUID = Query(..., description="User ID for authorization"),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Get details of a specific API key."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id,
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        status=api_key.status.value,
        rate_limit=api_key.rate_limit,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
    )


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: UUID,
    request: APIKeyUpdate,
    user_id: UUID = Query(..., description="User ID for authorization"),
    db: AsyncSession = Depends(get_db),
) -> APIKeyResponse:
    """Update an API key's settings."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id,
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Update fields if provided
    if request.name is not None:
        api_key.name = request.name

    if request.rate_limit is not None:
        api_key.rate_limit = request.rate_limit

    if request.status is not None:
        if request.status == "active":
            api_key.status = APIKeyStatus.ACTIVE
        elif request.status == "revoked":
            api_key.status = APIKeyStatus.REVOKED
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Use 'active' or 'revoked'."
            )

    await db.commit()
    await db.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        status=api_key.status.value,
        rate_limit=api_key.rate_limit,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
    )


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    user_id: UUID = Query(..., description="User ID for authorization"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Revoke an API key (soft delete)."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id,
        )
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.status = APIKeyStatus.REVOKED
    await db.commit()

    return {"message": "API key revoked successfully", "key_id": str(key_id)}


@router.post("/{key_id}/rotate", response_model=APIKeyCreatedResponse)
async def rotate_api_key(
    key_id: UUID,
    user_id: UUID = Query(..., description="User ID for authorization"),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreatedResponse:
    """
    Rotate an API key.

    Creates a new key with the same settings and revokes the old one.
    """
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == user_id,
        )
    )
    old_key = result.scalar_one_or_none()

    if not old_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Generate new key
    raw_key, key_hash, key_prefix = generate_api_key()

    # Create new key with same settings
    new_key = APIKey(
        user_id=user_id,
        name=f"{old_key.name} (rotated)",
        key_hash=key_hash,
        key_prefix=key_prefix,
        rate_limit=old_key.rate_limit,
        expires_at=old_key.expires_at,
    )

    # Revoke old key
    old_key.status = APIKeyStatus.REVOKED

    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return APIKeyCreatedResponse(
        id=new_key.id,
        name=new_key.name,
        key=raw_key,
        key_prefix=new_key.key_prefix,
        status=new_key.status.value,
        rate_limit=new_key.rate_limit,
        created_at=new_key.created_at,
        expires_at=new_key.expires_at,
    )
