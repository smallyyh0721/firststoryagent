"""
Story data models
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Genre(str, Enum):
    """Story genres"""
    FANTASY = "Fantasy"
    SCIFI = "Sci-Fi"
    ROMANCE = "Romance"
    MYSTERY = "Mystery"
    HORROR = "Horror"
    ADVENTURE = "Adventure"
    DRAMA = "Drama"
    COMEDY = "Comedy"
    THRILLER = "Thriller"
    OTHER = "Other"


class Status(str, Enum):
    """Story status"""
    DRAFT = "Draft"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    PUBLISHED = "Published"


class StoryBase(BaseModel):
    """Base story model"""
    title: str = Field(..., description="Story title")
    genre: Genre = Field(default=Genre.FANTASY, description="Story genre")
    status: Status = Field(default=Status.DRAFT, description="Story status")
    content: Optional[str] = Field(None, description="Story content")


class StoryCreate(StoryBase):
    """Model for creating a new story"""
    prompt: str = Field(..., description="Story generation prompt")


class StoryUpdate(BaseModel):
    """Model for updating a story"""
    title: Optional[str] = None
    genre: Optional[Genre] = None
    status: Optional[Status] = None
    content: Optional[str] = None


class Story(StoryBase):
    """Complete story model"""
    id: str = Field(..., description="Notion page ID")
    word_count: int = Field(..., description="Word count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    url: str = Field(..., description="Notion page URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc123",
                "title": "The Dragon's Quest",
                "genre": "Fantasy",
                "status": "In Progress",
                "content": "Once upon a time...",
                "word_count": 1500,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T14:20:00Z",
                "url": "https://www.notion.so/abc123"
            }
        }


class StoryListResponse(BaseModel):
    """Response model for listing stories"""
    stories: list[Story]
    total: int


class StoryGenerateRequest(BaseModel):
    """Request model for story generation"""
    prompt: str = Field(..., description="Story prompt or idea")
    genre: Genre = Field(default=Genre.FANTASY, description="Desired genre")
    length: str = Field(default="medium", description="Story length: short, medium, or long")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Write a story about a young wizard discovering ancient magic",
                "genre": "Fantasy",
                "length": "medium"
            }
        }


class StoryGenerateResponse(BaseModel):
    """Response model for story generation"""
    story: Story
    message: str = Field(..., description="Generation status message")