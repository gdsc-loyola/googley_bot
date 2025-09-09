from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TaskStatus(str, Enum):
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class Task(BaseModel):
    task_id: int = Field(..., description="Unique ID of the task")
    description: str = Field(..., description="Task details")
    status: TaskStatus = Field(..., description="Current task status")


class SheetResponse(BaseModel):
    range: str
    majorDimension: str
    values: List[List[str]]  # raw from Google API


class TaskList(BaseModel):
    tasks: List[Task]
