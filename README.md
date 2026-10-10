# GumShoo - Social Media Safety Detector

GumShoo is a professional social media safety detection application that analyzes content for risk across four domains: deepfake images, sentiment analysis, fraud detection, and propaganda detection.

## Features

- **Deepfake Analyzer**: Detect AI-generated or manipulated images
- **Sentiment Analysis**: Analyze sentiment in text posts and documents
- **Fraud Detection**: Identify fraudulent messages, ads, and transactions
- **Propaganda Detection**: Detect propaganda and manipulative content

## Installation (Windows PowerShell)

### Prerequisites

- Python 3.12 or higher
- Windows PowerShell

### Setup Steps

1. Clone or download this repository

2. Create a virtual environment:
```powershell
python -m venv venv
```

3. Activate the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
```

If you encounter an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

4. Install dependencies:
```powershell
pip install -r requirements.txt
```

5. (Optional) Copy `.env.example` to `.env` and configure:
```powershell
Copy-Item .env.example .env
```

## Running the Application

1. Ensure your virtual environment is activated

2. Start the Streamlit application:
```powershell
streamlit run app/Home.py
```

3. Open your web browser to the displayed URL (typically http://localhost:8501)

## Project Structure

```
app/            Streamlit entry point and pages
core/           Tool registry, result schema, input readers, settings
tools/          Detection tool implementations (one package per tool)
models/         Model files and model cards (gitignored)
assets/         CSS styling and theme configuration
tests/          Pytest test suite
legacy/         Legacy prototype (read-only reference)
```

## Configuration

Application settings are managed in `config.yaml`. Key settings include:

- `max_file_size_mb`: Maximum upload file size (default: 10 MB)
- `max_texts_per_batch`: Maximum number of texts to process at once (default: 500)
- `url_timeout_seconds`: Timeout for URL fetching (default: 10 seconds)
- `max_url_size_mb`: Maximum size for fetched URLs (default: 5 MB)

## Development

### Running Tests

```powershell
pytest
```

### Code Quality

Check code quality with ruff:
```powershell
ruff check .
```

### Type Checking

The codebase uses type hints throughout. Verify with a type checker if desired:
```powershell
# Using mypy (install separately)
mypy core/ tools/ app/
```

## Important Notes

- **All results are estimates, not verdicts**: Analysis results indicate probability and should be interpreted with appropriate context and domain expertise
- **Demo mode**: The foundation uses stub implementations. Real model integration requires separate configuration
- **Data privacy**: Uploaded content is processed in memory only and is never persisted to disk or logged
- **Security**: Input readers enforce SSRF protection and validate all external inputs

## Architecture

GumShoo uses a plugin-based architecture:

1. **Tool Registry**: Central registration system for analysis tools
2. **Result Schema**: Standardized result format across all tools
3. **Input Readers**: Secure input handling with validation
4. **Navigation**: Multi-page Streamlit application with session state management

Tools register themselves at startup and are discovered dynamically by the application.

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact your system administrator.
