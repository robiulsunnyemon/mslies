from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_db, disconnect_db
from app.api import router as api_router
from app.api.auth_api import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(
    title="RAG MCQ Generator",
    description="Generate MCQs from PDF and PPTX files using Langchain, Chroma, and Gemini",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the RAG MCQ Generator API"}
