from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    fullname: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    isVerified: bool
    createdAt: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

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
    mcqSets: List[MCQSetSchema] = []

    class Config:
        from_attributes = True

class UserMeResponse(UserResponse):
    files: List[FileResponse] = []

class GenerateRequest(BaseModel):
    topic: Optional[str] = None
    num_questions: int = Field(default=5, ge=1, le=20)
