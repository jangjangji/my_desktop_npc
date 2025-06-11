from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from config.database import Base
import pytz

seoul_tz = pytz.timezone('Asia/Seoul')

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    original_content = Column(Text)
    summarized_content = Column(Text)
    category = Column(String, default='auto')
    tags = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 