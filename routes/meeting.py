from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from config.database import get_db
from models.meeting import Meeting

router = APIRouter()

class MeetingCreate(BaseModel):
    title: str
    original_content: str
    summarized_content: str
    tags: Optional[str] = None
    category: Optional[str] = None

class MeetingResponse(BaseModel):
    id: int
    title: str
    original_content: str
    summarized_content: str
    created_at: datetime
    updated_at: Optional[datetime]
    tags: Optional[str]
    category: Optional[str]

    class Config:
        orm_mode = True

@router.post("/meetings/", response_model=MeetingResponse)
def create_meeting(meeting: MeetingCreate, db: Session = Depends(get_db)):
    db_meeting = Meeting(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting

@router.get("/meetings/", response_model=List[MeetingResponse])
def get_meetings(
    skip: int = 0, 
    limit: int = 10, 
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Meeting)
    
    if category:
        query = query.filter(Meeting.category == category)
    if tag:
        query = query.filter(Meeting.tags.contains(tag))
    
    return query.order_by(Meeting.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/meetings/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

@router.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    db.delete(meeting)
    db.commit()
    return {"status": "success", "message": "Meeting deleted"} 