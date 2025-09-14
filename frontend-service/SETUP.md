# Frontend Service Setup Guide

This guide will help you set up the Flask frontend service for the Phototype application.

## Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

## Installation Steps

### 1. Navigate to the frontend-service directory
```bash
cd frontend-service
```

### 2. Create a virtual environment (recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Flask dependencies
```bash
pip install flask werkzeug
```

Or install all project dependencies:
```bash
pip install -r ../requirements.txt
```

### 4. Run the Flask application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Directory Structure
```
frontend-service/
├── app.py                          # Main Flask application
├── static/                         # Static assets
│   ├── css/                       # Stylesheets
│   │   ├── json-basic.css         # Basic JSON viewer styles
│   │   └── json-comparison.css    # Comparison view styles
│   └── js/                        # JavaScript modules
│       ├── app.js                 # Main application orchestrator
│       ├── components.js          # UI components
│       ├── config.js              # Configuration
│       ├── upload.js              # File upload functionality
│       ├── utils.js               # Utility functions
│       └── visualizer.js          # JSON visualization
├── templates/                      # Jinja2 templates
│   ├── index.html                 # Main upload page
│   ├── view_json.html             # JSON viewer
│   ├── view_json_basic.html       # Basic JSON view
│   ├── view_json_comparison.html  # Comparison view
│   ├── error.html                 # Error page
│   └── errors/                    # Error templates
│       ├── 404.html
│       └── 500.html
├── uploads/                        # PDF upload directory
└── json/                          # JSON output directory
```

## Features
- **PDF Upload**: Drag-and-drop PDF file upload
- **JSON Visualization**: Interactive JSON data viewer with syntax highlighting
- **Multiple View Modes**: Basic and comparison view templates
- **Responsive Design**: Modern dark theme with Tailwind CSS
- **Modular JavaScript**: ES6 modules for maintainable code
- **Error Handling**: Comprehensive error pages and validation

## Troubleshooting

### Import Errors
If you see "Import 'flask' could not be resolved" errors:
1. Make sure Flask is installed: `pip install flask`
2. Activate your virtual environment if using one
3. Check that you're using the correct Python interpreter

### Template Lint Errors
The Jinja2 template syntax in HTML files may show lint errors in some editors. This is normal and expected for Flask templates.

### Static Files Not Loading
Ensure the static folder structure is correct and files are in the right locations:
- CSS files in `static/css/`
- JavaScript files in `static/js/`