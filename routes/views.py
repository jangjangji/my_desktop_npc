from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from config.database import get_db
from models.meeting import Meeting

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/meetings", response_class=HTMLResponse)
async def meetings_page(
    request: Request,
    page: int = 1,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db)
):
    per_page = 9  # 한 페이지당 보여줄 회의록 수
    query = db.query(Meeting)
    
    if category:
        query = query.filter(Meeting.category == category)
    if tag:
        query = query.filter(Meeting.tags.contains(tag))
    
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    
    meetings = query.order_by(Meeting.created_at.desc()) \
        .offset((page - 1) * per_page) \
        .limit(per_page) \
        .all()
    
    return templates.TemplateResponse("meeting_list.html", {
        "request": request,
        "meetings": meetings,
        "page": page,
        "total_pages": total_pages,
        "category": category or "",
        "tag": tag or ""
    })

@router.get("/meeting", response_class=HTMLResponse)
async def meeting_form(request: Request):
    return templates.TemplateResponse("meeting_form.html", {
        "request": request
    })

@router.get("/meetings/{meeting_id}", response_class=HTMLResponse)
async def meeting_detail(
    request: Request,
    meeting_id: int,
    db: Session = Depends(get_db)
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        return templates.TemplateResponse("404.html", {
            "request": request
        }, status_code=404)
    
    return templates.TemplateResponse("meeting_detail.html", {
        "request": request,
        "meeting": meeting
    }) 