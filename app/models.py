from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class Photo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id")
    filename: str
    caption: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Trip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    story: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    slug: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    photos: List[Photo] = Relationship(back_populates=None)
