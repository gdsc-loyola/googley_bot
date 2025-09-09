from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class TaskStatusEnum(str, enum.Enum):
    TODO = "Todo"
    IN_PROGRESS = "In Progress"
    DONE = "Done"


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.TODO)
