/**
 * Configuration and constants for Phototype application
 */
export const CONFIG = {
    APP_NAME: 'Phototype',
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_EXTENSIONS: ['pdf'],
    UPLOAD_ENDPOINT: '/upload',
    API_BASE: '/api',
    
    // UI Configuration
    THEMES: {
        primary: '#3b82f6',
        accent: '#10b981',
        background: '#1f2937',
        surface: '#374151',
        text: '#f9fafb',
        textSecondary: '#9ca3af'
    },
    
    // Animation timings
    TRANSITIONS: {
        fast: 200,
        normal: 300,
        slow: 500
    }
};

export const ENDPOINTS = {
    upload: '/upload',
    listJson: '/api/list-json',
    apiGetJson: (filename) => `/api/json/${filename}`,
    viewJson: (filename) => `/view/${filename}`,
    downloadJson: (filename) => `/api/json/${filename}`,
    home: '/'
};

export const MESSAGES = {
    upload: {
        success: 'PDF processed successfully!',
        error: 'Upload failed. Please try again.',
        processing: 'Processing PDF...',
        invalidFile: 'Only PDF files are allowed',
        fileTooBig: 'File too large. Maximum size is 10MB',
        noFile: 'Please select a file'
    },
    data: {
        loadError: 'Failed to load data',
        noData: 'No data available',
        invalidData: 'Invalid data format'
    },
    general: {
        loading: 'Loading...',
        error: 'An error occurred',
        success: 'Operation completed successfully'
    }
};