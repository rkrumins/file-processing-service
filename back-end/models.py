# models.py
import time
import uuid
from beanie import Document, Indexed
from pydantic import Field, BaseModel
from typing import Optional

# Plain Pydantic model for data transfer and in-memory storage
class TaskData(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"
    progress: int = 0
    file_location: str
    original_filename: str
    created_at: float = Field(default_factory=time.time)
    error_message: Optional[str] = None

    class Config:
        # Pydantic v2 config
        pass

# Beanie Document model for MongoDB
class Task(Document, TaskData):  # Inherit from TaskData to share fields
    # task_id is already defined in TaskData and will be used by Beanie
    # We need to ensure Beanie's Indexed is applied if it's the primary way to query
    task_id: Indexed(str, unique=True) = Field(default_factory=lambda: str(uuid.uuid4()))

    class Settings:
        name = None  # Will be overridden dynamically based on config