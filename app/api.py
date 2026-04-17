import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from typing import List
from app.database import db
from app.schemas import FileResponse, MCQSetSchema, GenerateRequest
from app.services.parser import parse_file
from app.services.rag import embed_document, generate_mcqs

router = APIRouter()

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

import cloudinary.uploader

from fastapi.concurrency import run_in_threadpool

async def process_file_background(file_id: str, filepath: str, file_type: str):
    try:
        await db.file.update(where={"id": file_id}, data={"status": "PROCESSING"})
        
        # run_in_threadpool allows us to run blocking sync functions without freezing the main loop
        text = await run_in_threadpool(parse_file, filepath, file_type)
        success = await run_in_threadpool(embed_document, file_id, text)
        
        if success:
            await db.file.update(where={"id": file_id}, data={"status": "EMBEDDED"})
        else:
            await db.file.update(where={"id": file_id}, data={"status": "FAILED"})
    except Exception as e:
        await db.file.update(where={"id": file_id}, data={"status": "FAILED"})
        print(f"Background task failed: {e}")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


@router.post("/files/upload", response_model=FileResponse)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    filename = file.filename
    ext = filename.split(".")[-1].lower()
    
    if ext == "pdf":
        file_type = "PDF"
    elif ext in ["ppt", "pptx"]:
        file_type = "PPTX"
    else:
        raise HTTPException(status_code=400, detail="Only PDF and PPTX files are supported")
        
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # We upload the local file to cloudinary
        upload_result = cloudinary.uploader.upload(filepath, resource_type="raw")
        cloudinary_url = upload_result.get("secure_url")
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")
        
    db_file = await db.file.create(
        data={
            "filename": filename,
            "filepath": cloudinary_url,
            "fileType": file_type,
            "status": "PENDING"
        }
    )
    
    background_tasks.add_task(process_file_background, db_file.id, filepath, file_type)
    
    return db_file

@router.get("/files/{file_id}/status")
async def get_file_status(file_id: str):
    db_file = await db.file.find_unique(where={"id": file_id})
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    return {"id": db_file.id, "status": db_file.status}

@router.post("/mcqs/generate/{file_id}")
async def generate_mcqs_route(file_id: str, request: GenerateRequest):
    db_file = await db.file.find_unique(where={"id": file_id})
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if db_file.status != "EMBEDDED":
        raise HTTPException(status_code=400, detail=f"File is not completely processed. Current status: {db_file.status}")
        
    try:
        mcq_set = await generate_mcqs(file_id, request.topic, request.num_questions)
        return {"message": "MCQs generated successfully", "mcq_set_id": mcq_set.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcqs/{file_id}")
async def get_mcqs(file_id: str):
    mcq_sets = await db.mcqset.find_many(
        where={"fileId": file_id},
        include={"questions": True}
    )
    return mcq_sets

@router.delete("/clear-db")
async def clear_database():
    try:
        # 1. Clear PostgreSQL via Prisma
        # Deleting all files will cascade delete MCQSet and Question due to schema relations
        await db.file.delete_many()
        
        # 2. Clear Local ChromaDB folder
        CHROMA_DIR = "./chroma_db"
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
            os.makedirs(CHROMA_DIR, exist_ok=True)
            
        return {"message": "Database and Vector Store cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

@router.delete("/clear-storage")
async def clear_storage():
    try:
        import cloudinary.api
        # This will delete all 'raw' resources (PDF, PPTX) from Cloudinary
        # Note: This might require that the API Key has Admin access
        result = cloudinary.api.delete_all_resources(resource_type="raw")
        return {"message": "Cloudinary storage cleared successfully", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear storage: {str(e)}")
