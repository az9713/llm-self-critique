from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Domain
from src.schemas.domain import DomainCreate, DomainResponse

router = APIRouter()


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def create_domain(domain: DomainCreate, db: AsyncSession = Depends(get_db)):
    db_domain = Domain(
        workspace_id=domain.workspace_id,
        name=domain.name,
        description=domain.description,
    )
    db.add(db_domain)
    await db.commit()
    await db.refresh(db_domain)
    return db_domain


@router.get("", response_model=list[DomainResponse])
async def list_domains(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Domain))
    return result.scalars().all()


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(domain_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Domain).where(Domain.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain
