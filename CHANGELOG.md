# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Initial project structure for modular OCR system
  - `frontend-service/` with Flask, HTML, JS, templates, static files
  - `router/` with services:
    - Language detection
    - OCR (English, Russian)
    - Preprocessor
    - Postprocessor
    - Router service
  - `common/utils/` for shared code
- Root files: `README.md`, `requirements.txt`, `CHANGELOG.md`
- `.phototype_venv/` and other venv dirs added to `.gitignore`

### Changed
- Migrated prototype into microservices layout

### Removed
- Extra placeholder folders for minimal structure
