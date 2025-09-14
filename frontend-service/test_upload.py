import requests
import os

# Test the upload endpoint
test_pdf_path = r"c:\Users\zhans\Desktop\projects\phototype\frontend-service\uploads\4392.pdf"

if os.path.exists(test_pdf_path):
    print(f"Testing upload with existing file: {test_pdf_path}")
    
    with open(test_pdf_path, 'rb') as f:
        files = {'file': ('test_upload.pdf', f, 'application/pdf')}
        
        try:
            response = requests.post('http://127.0.0.1:5000/upload', files=files)
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.json()}")
        except Exception as e:
            print(f"Error: {e}")
else:
    print(f"Test file not found: {test_pdf_path}")