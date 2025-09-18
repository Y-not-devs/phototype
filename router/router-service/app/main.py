import os
import asyncio
import aiohttp
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Router Service", version="1.0.0")

# Service URLs
PREPROCESSOR_SERVICE_URL = "http://127.0.0.1:8001"
LANG_DETECT_SERVICE_URL = "http://127.0.0.1:8002" 
OCR_EN_SERVICE_URL = "http://127.0.0.1:8003"
OCR_RU_SERVICE_URL = "http://127.0.0.1:8004"

class DocumentAnalysisResponse(BaseModel):
    filename: str
    language_detection: Optional[Dict[str, Any]] = None
    preprocessing_result: Optional[Dict[str, Any]] = None
    ocr_result: Optional[Dict[str, Any]] = None
    success: bool
    message: str

@app.get("/healthz")
def health_check():
    return {"status": "ok", "service": "router"}

@app.post("/analyze-document", response_model=DocumentAnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    """
    Complete document analysis pipeline:
    1. Try language detection directly from PDF
    2. If no text layer, use preprocessor -> OCR -> language detection
    3. Return comprehensive analysis results
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_content = await file.read()
    
    # Step 1: Try direct language detection from PDF
    language_result = await detect_language_from_pdf(file_content, file.filename)
    
    if language_result and language_result.get("success"):
        # PDF has text layer, language detected successfully
        return DocumentAnalysisResponse(
            filename=file.filename,
            language_detection=language_result,
            success=True,
            message="Language detected from PDF text layer"
        )
    
    # Step 2: PDF has no text layer or language detection failed
    # Use preprocessor -> OCR -> language detection pipeline
    try:
        # Preprocess the PDF
        preprocessing_result = await preprocess_pdf(file_content, file.filename)
        
        if not preprocessing_result or not preprocessing_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail="Preprocessing failed"
            )
        
        # Extract text using OCR (we'll use English OCR by default)
        # In a real implementation, we could use language hints or try multiple OCR engines
        ocr_result = await extract_text_with_ocr(preprocessing_result["data"], "en")
        
        if not ocr_result or not ocr_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail="OCR text extraction failed"
            )
        
        # Detect language from extracted text
        extracted_text = ocr_result["data"].get("text", "")
        if extracted_text.strip():
            language_result = await detect_language_from_text(extracted_text)
        
        return DocumentAnalysisResponse(
            filename=file.filename,
            language_detection=language_result,
            preprocessing_result=preprocessing_result,
            ocr_result=ocr_result,
            success=True,
            message="Language detected from OCR text extraction"
        )
        
    except Exception as e:
        return DocumentAnalysisResponse(
            filename=file.filename,
            success=False,
            message=f"Document analysis failed: {str(e)}"
        )

async def detect_language_from_pdf(file_content: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """Try to detect language directly from PDF text layer"""
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename, content_type='application/pdf')
            
            async with session.post(
                f"{LANG_DETECT_SERVICE_URL}/detect-language",
                data=data,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"success": True, "data": result}
                elif response.status == 422:
                    # No text layer in PDF
                    return {"success": False, "reason": "no_text_layer"}
                else:
                    return {"success": False, "reason": f"http_error_{response.status}"}
                    
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}

async def detect_language_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Detect language from extracted text"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"text": text}
            
            async with session.post(
                f"{LANG_DETECT_SERVICE_URL}/detect-text",
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "reason": f"http_error_{response.status}"}
                    
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}

async def preprocess_pdf(file_content: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """Preprocess PDF using the preprocessor service"""
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', file_content, filename=filename, content_type='application/pdf')
            
            async with session.post(
                f"{PREPROCESSOR_SERVICE_URL}/preprocess/",
                data=data,
                timeout=60
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"success": True, "data": result}
                else:
                    return {"success": False, "reason": f"http_error_{response.status}"}
                    
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}

async def extract_text_with_ocr(preprocessing_data: Dict[str, Any], language: str = "en") -> Optional[Dict[str, Any]]:
    """Extract text from preprocessed images using OCR"""
    # This is a placeholder implementation
    # In a real scenario, you would:
    # 1. Take the segmented images from preprocessing_data
    # 2. Send them to the appropriate OCR service based on detected/specified language
    # 3. Combine the OCR results into coherent text
    
    # For now, we'll return a mock successful response
    # because the OCR services are not enabled in run.py
    
    try:
        saved_files = preprocessing_data.get("saved_files", [])
        
        # Mock OCR extraction
        # In reality, you would process each image file through OCR
        mock_text = "This is extracted text from OCR processing. " * len(saved_files)
        
        return {
            "success": True,
            "data": {
                "text": mock_text,
                "processed_files": saved_files,
                "ocr_language": language,
                "method": "mock_ocr"  # Remove this in real implementation
            }
        }
        
    except Exception as e:
        return {"success": False, "reason": f"exception: {str(e)}"}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
