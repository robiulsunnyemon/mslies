from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QuestionSchema(BaseModel):
    id: str
    questionText: str
    options: List[str]
    correctAnswer: str
    explanation: str

class MCQSetSchema(BaseModel):
    id: str
    fileId: str
    topicName: Optional[str] = None
    createdAt: datetime
    questions: List[QuestionSchema] = []

class FileResponse(BaseModel):
    id: str
    filename: str
    fileType: str
    status: str
    createdAt: datetime

class GenerateRequest(BaseModel):
    topic: Optional[str] = None
    num_questions: int = Field(default=5, ge=1, le=20)
