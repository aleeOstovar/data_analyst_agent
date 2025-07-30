from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
import os
from typing import Optional

from ...models.schemas import AnalysisRequest, AnalysisResponse, ErrorResponse
from ...services.analysis import AnalysisService
from ...config.settings import UPLOAD_DIR

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse, responses={400: {"model": ErrorResponse}})
async def analyze_data(request: AnalysisRequest):
    """Analyze data based on the provided query"""
    try:
        service = AnalysisService()
        result = await service.process_analysis_request(
            query=request.query,
            file_path=request.file_path,
            code=request.code,
            thread_id=request.thread_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """Upload a data file for analysis"""
    try:
        # Save the file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        return {"filename": file.filename, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))