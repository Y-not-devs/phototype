"""
Main Flask application for Phototype - PDF to JSON conversion with visualization
"""
import os
import json
import sys
import uuid
import requests
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from services.pdf_excerpt_extractor import extract_pdf_excerpts

# Configuration
UPLOAD_FOLDER = '../uploads'  # Use root uploads folder
JSON_FOLDER = '../json'       # Use root json folder
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
SECRET_KEY = 'your-secret-key-change-in-production'

# Progress tracking storage
progress_storage = {}

class ProgressTracker:
    """Simple progress tracking for PDF processing tasks."""
    
    def __init__(self, task_id):
        self.task_id = task_id
        self.percentage = 0
        self.task = "Initializing..."
        self.details = "Starting processing..."
        self.status = "processing"
        self.start_time = time.time()
        progress_storage[task_id] = self
    
    def update(self, percentage, task="", details=""):
        """Update progress information."""
        self.percentage = max(0, min(100, percentage))
        if task:
            self.task = task
        if details:
            self.details = details
        if percentage >= 100:
            self.status = "complete"
    
    def to_dict(self):
        """Convert to dictionary for JSON response."""
        return {
            "task_id": self.task_id,
            "percentage": self.percentage,
            "task": self.task,
            "details": self.details,
            "status": self.status,
            "elapsed_time": time.time() - self.start_time
        }
    
    @staticmethod
    def get(task_id):
        """Get progress tracker by task ID."""
        return progress_storage.get(task_id)
    
    @staticmethod
    def cleanup_old():
        """Remove progress trackers older than 1 hour."""
        current_time = time.time()
        to_remove = []
        for task_id, tracker in progress_storage.items():
            if current_time - tracker.start_time > 3600:  # 1 hour
                to_remove.append(task_id)
        for task_id in to_remove:
            del progress_storage[task_id]

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_pdf_to_json(pdf_path, output_filename):
    """
    Mock PDF processing function.
    In a real implementation, this would use OCR and text extraction.
    For now, it creates a sample JSON structure.
    """
    sample_data = {
        "fields": {
            "contract_number": "AUTO_" + str(uuid.uuid4())[:8].upper(),
            "date": datetime.now().strftime("%d %B %Y"),
            "seller": {
                "name": "Extracted Company Name",
                "location": "Extracted Location",
                "representative": "Extracted Representative",
                "authority": "Extracted Authority Document"
            },
            "buyer": {
                "name": "Extracted Buyer Name", 
                "location": "Extracted Buyer Location",
                "director": "Extracted Director Name",
                "authority": "Extracted Buyer Authority"
            },
            "subject_of_contract": {
                "description": "Extracted contract description from PDF",
                "quantity": "Extracted quantity",
                "unit": "Extracted unit",
                "origin_country": "Extracted Origin Country"
            },
            "price_and_total_cost": {
                "price": "Pricing method extracted from PDF",
                "currency": "USD",
                "total_cost": "Amount extracted from PDF"
            },
            "delivery_documents": {
                "deadline": "Deadline extracted from PDF",
                "required_documents": [
                    "Invoice",
                    "Bill of Lading", 
                    "Certificate of Origin",
                    "Packing List"
                ]
            }
        },
        "text": f"Full text extracted from PDF file: {output_filename}",
        "metadata": {
            "processed_date": datetime.now().isoformat(),
            "source_file": output_filename,
            "processing_method": "Automated PDF extraction"
        }
    }
    
    return sample_data

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # Configure MIME types for JavaScript modules
    import mimetypes
    mimetypes.add_type('application/javascript', '.js')
    
    # Configure app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['JSON_FOLDER'] = JSON_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(JSON_FOLDER, exist_ok=True)
    
    # Start periodic cleanup of old progress trackers
    def cleanup_progress():
        while True:
            time.sleep(300)  # Run every 5 minutes
            ProgressTracker.cleanup_old()
    
    cleanup_thread = threading.Thread(target=cleanup_progress, daemon=True)
    cleanup_thread.start()

    @app.route("/")
    def index():
        """Main page with JSON data visualization."""
        json_files = []
        
        if os.path.exists(JSON_FOLDER):
            for filename in os.listdir(JSON_FOLDER):
                if filename.endswith('.json'):
                    json_files.append(filename)
        
        return render_template("index.html", json_files=json_files)

    @app.route("/view/<filename>")
    def view_json(filename):
        """View specific JSON file data with PDF comparison."""
        file_path = os.path.join(JSON_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return render_template('error.html', message='File not found'), 404
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Find corresponding PDF file
            base_name = os.path.splitext(filename)[0]
            pdf_url = f'/uploads/{base_name}.pdf'
            
            return render_template('view_json_comparison.html', 
                                 data=data, 
                                 filename=filename,
                                 pdf_url=pdf_url)
        except json.JSONDecodeError:
            return render_template('error.html', message='Invalid JSON file'), 400
        except Exception as e:
            return render_template('error.html', message=f'Error reading file: {str(e)}'), 500

    @app.route("/api/json/<filename>")
    def api_get_json(filename):
        """API endpoint to get JSON data."""
        file_path = os.path.join(JSON_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return jsonify(data)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON file'}), 400
        except Exception as e:
            return jsonify({'error': f'Error reading file: {str(e)}'}), 500

    @app.route("/uploads/<filename>")
    def serve_uploaded_file(filename):
        """Serve uploaded PDF files."""
        filename = secure_filename(filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path)

    @app.route("/api/list-json")
    def list_json():
        """API endpoint to list available JSON files."""
        json_files = []
        
        if os.path.exists(JSON_FOLDER):
            for filename in os.listdir(JSON_FOLDER):
                if filename.endswith('.json'):
                    file_path = os.path.join(JSON_FOLDER, filename)
                    try:
                        # Get file size and modification time
                        stat = os.stat(file_path)
                        file_info = {
                            'filename': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        }
                        json_files.append(file_info)
                    except Exception:
                        # If we can't get file info, just include the filename
                        json_files.append({'filename': filename})
        
        return jsonify({'success': True, 'files': [f['filename'] for f in json_files]})

    @app.route("/api/pdf-excerpts/<filename>")
    def get_pdf_excerpts(filename):
        """Extract text excerpts from PDF that correspond to JSON fields."""
        try:
            # Ensure safe filename
            filename = secure_filename(filename)
            
            # Load JSON data
            json_filename = filename.replace('.pdf', '.json')
            json_path = os.path.join(JSON_FOLDER, json_filename)
            
            if not os.path.exists(json_path):
                return jsonify({'error': 'JSON file not found'}), 404
                
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Find PDF file
            pdf_path = os.path.join(UPLOAD_FOLDER, filename)
            
            if not os.path.exists(pdf_path):
                return jsonify({'error': 'PDF file not found'}), 404
            
            # Extract excerpts
            excerpts = extract_pdf_excerpts(pdf_path, json_data)
            
            return jsonify({
                'success': True,
                'excerpts': excerpts,
                'filename': filename
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to extract excerpts: {str(e)}'}), 500

    @app.route("/upload", methods=['POST'])
    def upload_pdf():
        """Handle PDF upload, save to root uploads folder, and use existing backend pipeline."""
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        if file_length > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'File too large (max 16MB)'}), 400

        # Create task ID for progress tracking
        task_id = str(uuid.uuid4())
        tracker = ProgressTracker(task_id)
        
        try:
            tracker.update(5, "Uploading file", "Saving PDF file to server...")
            
            # Save the uploaded file to root uploads folder
            filename = secure_filename(file.filename or 'uploaded_file.pdf')
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Ensure the uploads directory exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(upload_path)
            
            tracker.update(15, "File uploaded", "PDF file saved successfully")
            
            # Generate JSON filename (same as PDF name but with .json extension)
            base_name = os.path.splitext(filename)[0]
            json_filename = f"{base_name}.json"
            json_path = os.path.join(JSON_FOLDER, json_filename)
            
            # Process in background thread
            def background_processing():
                try:
                    tracker.update(25, "Preprocessing document", "Analyzing document structure...")
                    
                    # Initialize with fallback data
                    json_data = process_pdf_to_json(upload_path, filename)
                    
                    # Try to use the existing backend preprocessor service
                    backend_success = False
                    try:
                        tracker.update(40, "Running OCR analysis", "Extracting text from PDF pages...")
                        
                        PREPROCESSOR_URL = "http://127.0.0.1:8001/preprocess/"
                        with open(upload_path, "rb") as f:
                            files = {"file": (filename, f, "application/pdf")}
                            resp = requests.post(PREPROCESSOR_URL, files=files, timeout=60)
                        
                        if resp.status_code == 200:
                            tracker.update(70, "Processing extracted text", "Organizing extracted information...")
                            
                            # Backend preprocessing succeeded
                            preprocessor_data = resp.json()
                            
                            # For now, create a simple JSON structure
                            # In a real setup, this would come from the complete backend pipeline
                            json_data = {
                                "fields": {
                                    "contract_number": f"AUTO_{base_name.upper()}",
                                    "date": datetime.now().strftime("%d %B %Y"),
                                    "seller": {
                                        "name": "Extracted from preprocessor data",
                                        "location": "Location from OCR",
                                        "representative": "Representative from document",
                                        "authority": "Authority document reference"
                                    },
                                    "buyer": {
                                        "name": "Buyer extracted from PDF",
                                        "location": "Buyer location",
                                        "director": "Director name",
                                        "authority": "Authority document"
                                    },
                                    "subject_of_contract": {
                                        "description": "Contract subject extracted by backend OCR",
                                        "origin_country": "Origin country from document"
                                    },
                                    "price_and_total_cost": {
                                        "price": "Price extracted from document",
                                        "currency": "Currency from OCR",
                                        "total_cost": "Total cost from backend processing"
                                    }
                                },
                                "metadata": {
                                    "processed_date": datetime.now().isoformat(),
                                    "source_file": filename,
                                    "processing_method": "Backend OCR with preprocessor",
                                    "preprocessor_data": preprocessor_data
                                }
                            }
                            backend_success = True
                            print(f"Backend preprocessing successful for {filename}")
                        else:
                            print(f"Backend preprocessor error: {resp.status_code} - {resp.text}")
                            tracker.update(50, "Using fallback processing", "Backend unavailable, using local processing...")
                    except Exception as e:
                        print(f"Backend preprocessor unavailable: {e}")
                        tracker.update(50, "Using fallback processing", "Backend unavailable, using local processing...")
                    
                    # Fallback to simple processing if backend is unavailable
                    if not backend_success:
                        json_data = process_pdf_to_json(upload_path, filename)
                        json_data["metadata"]["processing_method"] = "Local fallback processing"
                    
                    tracker.update(90, "Finalizing output", "Saving JSON file...")
                    
                    # Save JSON file to root json folder
                    os.makedirs(JSON_FOLDER, exist_ok=True)
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
                    tracker.update(100, "Processing complete", "JSON data generated successfully")
                    
                except Exception as e:
                    tracker.update(0, "Processing failed", f"Error: {str(e)}")
                    tracker.status = "error"
            
            # Start background processing
            threading.Thread(target=background_processing, daemon=True).start()
            
            return jsonify({
                'success': True, 
                'message': 'PDF upload started',
                'filename': filename,
                'json_filename': json_filename,
                'task_id': task_id,
                'redirect_url': f'/view/{json_filename}',
                'processing_method': 'async'
            })

        except Exception as e:
            # Clean up uploaded file if processing failed
            try:
                upload_path_var = locals().get('upload_path')
                if upload_path_var and os.path.exists(upload_path_var):
                    os.remove(upload_path_var)
            except:
                pass
            
            return jsonify({
                'success': False, 
                'error': f'Upload failed: {str(e)}'
            }), 500

    @app.route("/progress/<task_id>")
    def get_progress(task_id):
        """Get progress information for a processing task."""
        tracker = ProgressTracker.get(task_id)
        if not tracker:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify(tracker.to_dict())

    @app.route("/api/validation", methods=['POST'])
    def save_validation():
        """Save validation results for JSON fields."""
        try:
            data = request.get_json()
            filename = data.get('filename')
            field_path = data.get('field_path')
            status = data.get('status')  # 'approved' or 'rejected'
            
            if not all([filename, field_path, status]):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # For now, just return success - in a real app, you'd save to database
            return jsonify({'success': True, 'message': 'Validation saved'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # Template filter for pretty JSON
    @app.template_filter('tojsonpretty')
    def to_json_pretty(value):
        """Convert dictionary to pretty JSON string."""
        return json.dumps(value, indent=2, ensure_ascii=False)

    return app

if __name__ == "__main__":
    app = create_app()
    port = 5000
    if "--port" in sys.argv:
        i = sys.argv.index("--port")
        if i+1 < len(sys.argv):
            port = int(sys.argv[i+1])
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
