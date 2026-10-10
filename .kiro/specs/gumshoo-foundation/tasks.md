# Implementation Plan: GumShoo Foundation

## Overview

This implementation plan breaks down the GumShoo foundation into discrete coding tasks. The foundation includes a multi-page Streamlit application with plugin-based tool architecture, secure input handling, standardized result schema, professional theming, and comprehensive testing infrastructure. All four detection tools (Deepfake, Sentiment, Fraud, Propaganda) will use stub implementations returning clearly marked demo results.

## Tasks

- [ ] 1. Set up project structure and configuration
  - Create directory structure (app/, core/, tools/, models/, assets/, tests/)
  - Create .gitignore with entries for models/, datasets/, .env
  - Create config.yaml with application settings
  - Create .env.example template file
  - Create requirements.txt with pinned dependencies (streamlit, pandas, scikit-learn, torch, timm, transformers, vaderSentiment, pytest, ruff, python-dotenv, pyyaml, pillow, python-docx, openpyxl)
  - Create README.md with Windows PowerShell setup instructions
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_

- [ ] 2. Implement core services
  - [ ] 2.1 Implement result schema (core/schema.py)
    - Define AnalysisResult dataclass with validation
    - Implement score validation (0 to 1 range)
    - Add to_dict() and to_display_dict() methods
    - Include all required fields: label, score, model_name, model_version, is_demo, details, warnings
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [ ]* 2.2 Write unit tests for result schema (tests/test_schema.py)
    - Test score validation (valid range, out-of-range rejection)
    - Test to_dict() serialization
    - Test to_display_dict() formatting
    - Test all field assignments
    - _Requirements: 10.3_

  - [ ] 2.3 Implement tool registry (core/registry.py)
    - Define ToolMetadata dataclass
    - Implement ToolRegistry class with register(), get_tool(), get_tools_by_input_type(), list_all_tools(), get_tool_status() methods
    - Create global registry instance
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 2.4 Write unit tests for tool registry (tests/test_registry.py)
    - Test tool registration
    - Test tool retrieval by name
    - Test tool filtering by input type
    - Test duplicate registration handling
    - Test missing tool retrieval
    - _Requirements: 10.2_

  - [ ] 2.5 Implement settings management (core/settings.py)
    - Define Settings dataclass with frozen=True
    - Implement load() classmethod to read from config.yaml and .env
    - Create global settings instance
    - Include default values for all configuration options
    - _Requirements: 11.2, 11.3, 15.5_

  - [ ] 2.6 Implement navigation utilities (core/navigation.py)
    - Implement init_session_state() function
    - Implement navigate_to_input() function
    - Implement navigate_to_results() function
    - Implement navigate_to_home() function
    - _Requirements: 1.4, 2.1_

  - [ ] 2.7 Implement input readers with security validation (core/readers.py)
    - Define InputReader class with security constants
    - Implement read_image() method
    - Implement read_text_file() with encoding detection
    - Implement read_docx() to extract text and images
    - Implement read_csv() with auto-detection of text column
    - Implement fetch_url() with SSRF protection
    - Implement _validate_url_scheme() to allow only http/https
    - Implement _validate_url_host() to block private/loopback/link-local IPs
    - Implement _detect_csv_text_column() heuristic
    - Add timeout and size limits for URL fetching
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12_

  - [ ]* 2.8 Write unit tests for input readers (tests/test_readers.py)
    - Test image reading and validation
    - Test text file reading with various encodings
    - Test CSV parsing and column detection
    - Test URL scheme validation (reject file://, ftp://, etc.)
    - Test SSRF protection (block 127.0.0.1, 10.0.0.0/8, 192.168.0.0/16, etc.)
    - Test timeout and size limit enforcement
    - Test error handling for malformed files
    - _Requirements: 10.1_

- [ ] 3. Checkpoint - Core services complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement stub detection tools
  - [ ] 4.1 Implement Deepfake Analyzer stub (tools/deepfake/analyzer.py)
    - Implement analyze_image() function accepting PIL Image
    - Generate deterministic fake score using MD5 hash of image bytes
    - Return AnalysisResult with is_demo=True
    - Include warnings about demo mode
    - Register tool in tools/deepfake/__init__.py
    - _Requirements: 12.1, 12.5, 12.6, 12.7, 4.1, 4.2, 4.3, 4.4_

  - [ ] 4.2 Implement Sentiment Analysis stub (tools/sentiment/analyzer.py)
    - Implement analyze_text() function accepting str or List[str]
    - Generate deterministic sentiment using hash of text
    - Return AnalysisResult or List[AnalysisResult] with is_demo=True
    - Support batch processing for list input
    - Register tool in tools/sentiment/__init__.py
    - _Requirements: 12.2, 12.5, 12.6, 12.7, 4.1, 4.2, 4.3, 4.4_

  - [ ] 4.3 Implement Fraud Detection stub (tools/fraud/detector.py)
    - Implement detect_fraud() function accepting str
    - Use simple keyword matching plus hash-based score
    - Return AnalysisResult with is_demo=True
    - Register tool in tools/fraud/__init__.py
    - _Requirements: 12.3, 12.5, 12.6, 12.7, 4.1, 4.2, 4.3, 4.4_

  - [ ] 4.4 Implement Propaganda Detection stub (tools/propaganda/detector.py)
    - Implement detect_propaganda() function accepting str
    - Generate deterministic score using hash
    - Return AnalysisResult with is_demo=True
    - Register tool in tools/propaganda/__init__.py
    - _Requirements: 12.4, 12.5, 12.6, 12.7, 4.1, 4.2, 4.3, 4.4_

  - [ ]* 4.5 Write unit tests for stub tools (tests/test_tools.py)
    - Test each tool returns valid AnalysisResult
    - Test is_demo flag is always True
    - Test score is in valid range [0, 1]
    - Test batch processing for sentiment tool
    - Verify tools are properly registered
    - _Requirements: 10.1, 10.2, 10.3_

- [ ] 5. Implement theme and styling
  - [ ] 5.1 Create CSS stylesheet (assets/style.css)
    - Define color palette (ink, muted, line, plum, lavender, soft pink, soft green)
    - Import Google Fonts (Source Serif 4, Inter)
    - Style typography (headings with serif, body with sans-serif)
    - Style topbar navigation component
    - Style module number eyebrow
    - Style buttons, file uploader, metrics
    - Ensure WCAG AA contrast ratios for all text
    - Remove all emoji characters
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.8, 7.9, 7.10_

  - [ ] 5.2 Create Streamlit theme configuration (assets/.streamlit/config.toml)
    - Configure primary color (plum)
    - Configure background colors (white, lavender)
    - Configure text color (ink)
    - Configure font (sans serif)
    - Set server.headless = true
    - _Requirements: 7.7_

- [ ] 6. Implement application pages
  - [ ] 6.1 Implement Welcome page (app/Home.py)
    - Set page config with title and layout
    - Load and apply custom CSS
    - Initialize session state
    - Display topbar navigation
    - Display title and description
    - Retrieve all tools from registry
    - Display four tool cards in 2x2 grid layout
    - Label cards as "Module 01-04" with display names
    - Show tool status (loaded/fallback/demo)
    - Navigate to Input page on card click
    - Display disclaimer about estimates vs verdicts
    - Remove all emoji characters
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 7.8, 8.1, 8.2, 8.3, 8.4_

  - [ ] 6.2 Implement Input page (pages/1_Input.py)
    - Set page config
    - Load and apply custom CSS
    - Check for selected tool in session state
    - Display topbar and tool information
    - Offer three input methods: Upload File, Paste Text, Enter URL
    - Implement file upload with extension validation (.png, .jpg, .jpeg, .webp, .docx, .txt, .csv)
    - Implement text paste with processing mode selection (whole document vs separate posts)
    - Implement URL input with content fetching
    - Validate file size limits
    - Display clear error messages for validation failures
    - Use InputReader for all input processing
    - Call tool's analyze function on valid input
    - Navigate to Results page after successful analysis
    - Handle errors gracefully with user-friendly messages
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 14.1, 14.2, 14.3, 14.4, 14.5, 15.1, 15.2, 15.3, 15.4_

  - [ ] 6.3 Implement Results page (pages/2_Results.py)
    - Set page config
    - Load and apply custom CSS
    - Check for result in session state
    - Display topbar navigation
    - Display prominent disclaimer: "estimate, not a verdict"
    - Display demo mode indicator when is_demo=True
    - Render single result with metrics (label, confidence, model)
    - Render multiple results as DataFrame for batch processing
    - Display all Result_Schema fields (label, score, details, warnings, model_name, model_version)
    - Offer CSV download of results
    - Offer JSON download of results
    - Provide "Analyze Another" button
    - Provide "Back to Home" button
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12_

- [ ] 7. Create model cards and documentation
  - [ ] 7.1 Create model card stubs (models/model_cards/)
    - Create deepfake.md describing Xception ensemble architecture
    - Create sentiment.md describing transformer-based approach
    - Create fraud.md describing ML-based fraud detection
    - Create propaganda.md describing propaganda classification
    - Mark all as "Demo Mode - Stub Implementation" in each card
    - _Requirements: 13.4_

  - [ ] 7.2 Create .gitkeep for models directory
    - Add models/.gitkeep to preserve empty directory structure
    - _Requirements: 11.6, 13.4_

- [ ] 8. Implement code quality and type hints
  - [ ] 8.1 Add type hints to all modules
    - Add type hints to all public functions in core/
    - Add type hints to all public functions in tools/
    - Add type hints to all page modules in app/
    - Use typing module for complex types (List, Dict, Tuple, Optional, Union, Callable, Literal)
    - _Requirements: 10.5_

  - [ ] 8.2 Add docstrings to all modules
    - Add module-level docstrings
    - Add class docstrings with descriptions
    - Add function docstrings with Args, Returns, Raises sections
    - Follow Google or NumPy docstring format
    - _Requirements: 10.6, 10.7_

  - [ ]* 8.3 Run ruff and fix violations
    - Execute ruff check on entire codebase
    - Fix all linting violations
    - Ensure zero violations remain
    - _Requirements: 10.4_

- [ ] 9. Final integration and testing
  - [ ] 9.1 Wire all components together
    - Ensure all tools are imported and registered at startup
    - Verify session state initialization in all pages
    - Verify navigation flows correctly between pages
    - Verify CSS is loaded in all pages
    - Test end-to-end workflow: Home → Input → Results
    - _Requirements: 1.4, 2.1_

  - [ ]* 9.2 Run all tests
    - Execute pytest on entire test suite
    - Verify all tests pass
    - Check test coverage
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ]* 9.3 Manual testing on Windows PowerShell
    - Test application startup with `streamlit run app/Home.py`
    - Test each tool with different input types
    - Test file uploads (various formats)
    - Test URL fetching with valid and invalid URLs
    - Test CSV batch processing
    - Test error handling scenarios
    - Verify theme renders correctly
    - Verify no emoji characters appear anywhere
    - Test result export (CSV and JSON)
    - _Requirements: 11.5_

- [ ] 10. Final checkpoint - Complete implementation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- All stub tools must set is_demo=True and include warnings
- No real model weights should be loaded or committed
- All user content processing must be memory-only (no disk persistence, no logging)
- SSRF protection is critical for URL fetching - test thoroughly
- WCAG AA contrast requirements must be validated for all text
- All emoji characters must be removed from UI, code, and documentation
- Windows PowerShell compatibility must be maintained throughout

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.3", "2.5", "2.6"] },
    { "id": 2, "tasks": ["2.2", "2.4", "2.7"] },
    { "id": 3, "tasks": ["2.8", "4.1", "4.2", "4.3", "4.4", "5.1", "5.2"] },
    { "id": 4, "tasks": ["4.5", "6.1", "6.2", "6.3", "7.1", "7.2"] },
    { "id": 5, "tasks": ["8.1", "8.2"] },
    { "id": 6, "tasks": ["8.3", "9.1"] },
    { "id": 7, "tasks": ["9.2", "9.3"] }
  ]
}
```
