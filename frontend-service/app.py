"""
Main Flask application for Phototype - PDF to JSON conversion with visualization
"""
import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from services.pdf_excerpt_extractor import extract_pdf_excerpts

# Configuration
UPLOAD_FOLDER = 'uploads'
JSON_FOLDER = 'json'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
SECRET_KEY = 'your-secret-key-change-in-production'

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
    
    # Configure app
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['JSON_FOLDER'] = JSON_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
    
    # Create necessary directories
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(JSON_FOLDER, exist_ok=True)

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
        """Handle PDF file upload and processing."""
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type and size
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        file.seek(0)
        
        if file_length > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'File too large. Maximum size is 16MB'}), 400
        
        try:
            # Secure the filename
            if not file.filename:
                return jsonify({'success': False, 'error': 'Invalid filename'}), 400
                
            filename = secure_filename(file.filename)
            
            # Save uploaded file
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(upload_path)
            
            # Generate output filename for JSON
            json_filename = filename.rsplit('.', 1)[0] + '.json'
            
            # Process PDF to JSON (mock processing)
            json_data = process_pdf_to_json(upload_path, filename)
            
            # Save JSON data
            json_path = os.path.join(JSON_FOLDER, json_filename)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            # Clean up uploaded PDF file
            try:
                os.remove(upload_path)
            except:
                pass  # Don't fail if cleanup fails
            
            return jsonify({
                'success': True, 
                'message': 'PDF processed successfully',
                'filename': json_filename
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': f'Processing failed: {str(e)}'}), 500

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
    app.run(host="0.0.0.0", port=5000, debug=True)
