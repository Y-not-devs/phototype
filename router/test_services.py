import requests
import json
from pathlib import Path

def test_lang_detect_service():
    """Test the language detection service with a sample PDF"""
    
    # Test health endpoint
    try:
        health_resp = requests.get("http://127.0.0.1:8002/healthz", timeout=5)
        print(f"Health check: {health_resp.status_code} - {health_resp.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test with a sample PDF from uploads
    uploads_dir = Path("../uploads")
    pdf_files = list(uploads_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in uploads directory")
        return
    
    test_file = pdf_files[0]
    print(f"Testing with file: {test_file.name}")
    
    # Test language detection
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "application/pdf")}
            resp = requests.post(
                "http://127.0.0.1:8002/detect-language",
                files=files,
                timeout=30
            )
        
        print(f"Language detection status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print("Language detection successful!")
            print(f"Top language: {result.get('top_language')}")
            print(f"Document languages: {result.get('document_languages', [])[:3]}")  # Show top 3
            print(f"Chunks detected: {len(result.get('per_chunk', []))}")
        elif resp.status_code == 422:
            print("PDF has no text layer - OCR needed")
        else:
            print(f"Error: {resp.text}")
            
    except Exception as e:
        print(f"Language detection test failed: {e}")

def test_router_service():
    """Test the router service"""
    
    # Test health endpoint
    try:
        health_resp = requests.get("http://127.0.0.1:8000/healthz", timeout=5)
        print(f"Router health check: {health_resp.status_code} - {health_resp.json()}")
    except Exception as e:
        print(f"Router health check failed: {e}")
        return
    
    # Test with a sample PDF
    uploads_dir = Path("../uploads")
    pdf_files = list(uploads_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in uploads directory")
        return
    
    test_file = pdf_files[0]
    print(f"Testing router with file: {test_file.name}")
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file.name, f, "application/pdf")}
            resp = requests.post(
                "http://127.0.0.1:8000/analyze-document",
                files=files,
                timeout=60
            )
        
        print(f"Router analysis status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print("Document analysis successful!")
            print(f"Filename: {result.get('filename')}")
            print(f"Success: {result.get('success')}")
            print(f"Message: {result.get('message')}")
            
            lang_detection = result.get('language_detection')
            if lang_detection and lang_detection.get('success'):
                lang_data = lang_detection['data']
                print(f"Detected language: {lang_data.get('top_language')}")
        else:
            print(f"Error: {resp.text}")
            
    except Exception as e:
        print(f"Router test failed: {e}")

if __name__ == "__main__":
    print("Testing Language Detection Service...")
    test_lang_detect_service()
    print("\n" + "="*50 + "\n")
    print("Testing Router Service...")
    test_router_service()