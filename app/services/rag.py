import json
import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
from app.config import settings
from app.database import db

logger = logging.getLogger(__name__)

# Configure embeddings and LLM
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", 
    google_api_key=settings.GOOGLE_API_KEY
)

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    google_api_key=settings.GOOGLE_API_KEY, 
    temperature=0.3
)

# Chroma DB setup locally
CHROMA_DIR = "./chroma_db"

def embed_document(file_id: str, text: str):
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        
        # We store metadata for each chunk indicating which file it belongs to
        metadatas = [{"file_id": file_id} for _ in chunks]
        
        # Initialize chroma vector store for the collection
        vectorstore = Chroma(
            collection_name=file_id, 
            embedding_function=embeddings, 
            persist_directory=CHROMA_DIR
        )
        
        vectorstore.add_texts(texts=chunks, metadatas=metadatas)
        return True
    except Exception as e:
        logger.error(f"Error embedding document {file_id}: {e}")
        return False

# Pydantic models for structured output from Gemini
class MCQOption(BaseModel):
    options: List[str] = Field(description="List of 4 options (e.g. ['A', 'B', 'C', 'D'])")

class MCQItem(BaseModel):
    question: str = Field(description="The MCQ question")
    options: List[str] = Field(description="List of 4 strings representing the options")
    correct_answer: str = Field(description="The correct option from the options list")
    explanation: str = Field(description="Explanation of why this answer is correct")

class MCQResult(BaseModel):
    questions: List[MCQItem]

async def generate_mcqs(file_id: str, topic: str = None, num_questions: int = 5):
    vectorstore = Chroma(
        collection_name=file_id, 
        embedding_function=embeddings, 
        persist_directory=CHROMA_DIR
    )
    
    query = topic if topic else "Important concepts and core topics"
    # Retrieve top chunks based on the topic
    docs = vectorstore.similarity_search(query, k=5)
    context_text = "\n\n".join([doc.page_content for doc in docs])
    
    prompt = f"""
    Based on the following extracted text from a document, generate {num_questions} Multiple Choice Questions (MCQs) regarding the topic: "{query}".
    
    Context:
    {context_text}
    
    Format the output strictly as JSON following this schema:
    {{
        "questions": [
            {{
                "question": "question text",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "explanation reason"
            }}
        ]
    }}
    """
    
    try:
        structured_llm = llm.with_structured_output(MCQResult)
        result: MCQResult = structured_llm.invoke(prompt)
        
        # Save to DB
        mcq_set = await db.mcqset.create(
            data={
                "fileId": file_id,
                "topicName": topic,
                "questions": {
                    "create": [
                        {
                            "questionText": q.question,
                            "options": json.dumps(q.options),
                            "correctAnswer": q.correct_answer,
                            "explanation": q.explanation
                        } for q in result.questions
                    ]
                }
            }
        )
        return mcq_set
    except Exception as e:
        logger.error(f"Error generating MCQs for {file_id}: {e}")
        raise e
