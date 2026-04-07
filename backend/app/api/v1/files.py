"""File management API routes."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db, User, FileStorage
from app.models.schemas import FileInfo, FileListResponse, BaseResponse
from app.api.v1.auth import get_current_user

router = APIRouter()

# Upload directory
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("", response_model=FileListResponse)
async def list_files(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's uploaded files."""
    result = await db.execute(
        select(FileStorage)
        .where(FileStorage.user_id == current_user.id)
        .order_by(FileStorage.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    files = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(
        select(FileStorage).where(FileStorage.user_id == current_user.id)
    )
    total = len(count_result.scalars().all())
    
    return FileListResponse(
        files=[
            FileInfo(
                id=f.id,
                filename=f.filename,
                size=f.size,
                content_type=f.content_type,
                created_at=f.created_at
            )
            for f in files
        ],
        total=total
    )


@router.post("/upload", response_model=FileInfo)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a file."""
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = Path(file.filename).suffix
    stored_filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / stored_filename
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Save to database
    file_record = FileStorage(
        id=file_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        size=len(content),
        content_type=file.content_type or "application/octet-stream"
    )
    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)
    
    return FileInfo(
        id=file_record.id,
        filename=file_record.filename,
        size=file_record.size,
        content_type=file_record.content_type,
        created_at=file_record.created_at
    )


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download a file."""
    result = await db.execute(
        select(FileStorage).where(
            FileStorage.id == file_id,
            FileStorage.user_id == current_user.id
        )
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file_record.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_record.file_path,
        filename=file_record.filename,
        media_type=file_record.content_type
    )


@router.delete("/{file_id}", response_model=BaseResponse)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a file."""
    result = await db.execute(
        select(FileStorage).where(
            FileStorage.id == file_id,
            FileStorage.user_id == current_user.id
        )
    )
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from disk
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    # Delete from database
    await db.delete(file_record)
    await db.commit()
    
    return BaseResponse(message="File deleted successfully")
