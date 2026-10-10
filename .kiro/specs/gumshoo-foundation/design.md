# Design Document: GumShoo Foundation

## Overview

GumShoo is a social media safety detection application that provides analysts with tools to assess content risk across four domains: deepfake images, sentiment analysis, fraud detection, and propaganda detection. This design document describes the foundational architecture—the application shell, navigation system, input handling infrastructure, tool plugin system, result schema, theming, and quality infrastructure—built to support future integration of real detection models.

The foundation uses stub implementations for all four detection tools, returning clearly marked demo results. This enables validation of the architecture, user workflows, and integration points before investing in model training and optimization.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Application                │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Welcome     │  │    Input     │  │   Results    │ │
│  │   Page       │─→│    Page      │─→│    Page      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                            │                            │
│                    ┌───────▼────────┐                   │
│                    │  Core Services │                   │
│                    │                │                   │
│                    │  • Registry    │                   │
│                    │  • Schema      │                   │
│                    │  • Readers     │                   │
│                    │  • Settings    │                   │
│                    └───────┬────────┘                   │
│                            │                            │
│         ┌──────────────────┼──────────────────┐         │
│         │                  │                  │         │
│    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐    │
│    │Deepfake │       │Sentiment│       │  Fraud  │    │
│    │  Tool   │       │  Tool   │       │  Tool   │    │
│    └─────────┘       └─────────┘       └─────────┘    │
│         │                  │                  │         │
│    ┌────▼─────────────────▼──────────────────▼────┐    │
│    │          Tool Plugin Interface             │    │
│    └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Directory Structure

```
gumshoo/
├── app/
│   ├── Home.py                    # Entry point and welcome page
│   └── pages/
│       ├── 1_Input.py             # Shared input collection page
│       └── 2_Results.py           # Result display page
├── core/
│   ├── __init__.py
│   ├── registry.py                # Tool registration and discovery
│   ├── schema.py                  # Result schema definition
│   ├── readers.py                 # Input readers with security validation
│   ├── settings.py                # Configuration management
│   └── navigation.py              # Page navigation utilities
├── tools/
│   ├── __init__.py
│   ├── deepfake/
│   │   ├── __init__.py
│   │   └── analyzer.py            # Deepfake detection (stub)
│   ├── sentiment/
│   │   ├── __init__.py
│   │   └── analyzer.py            # Sentiment analysis (stub)
│   ├── fraud/
│   │   ├── __init__.py
│   │   └── detector.py            # Fraud detection (stub)
│   └── propaganda/
│       ├── __init__.py
│       └── detector.py            # Propaganda detection (stub)
├── models/
│   ├── .gitkeep
│   └── model_cards/
│       ├── deepfake.md
│       ├── sentiment.md
│       ├── fraud.md
│       └── propaganda.md
├── assets/
│   ├── style.css                  # Custom CSS styling
│   └── .streamlit/
│       └── config.toml            # Streamlit theme configuration
├── tests/
│   ├── __init__.py
│   ├── test_registry.py
│   ├── test_schema.py
│   ├── test_readers.py
│   └── test_tools.py
├── legacy/                        # Read-only reference (existing)
├── .env.example                   # Environment variable template
├── .gitignore
├── config.yaml                    # Application settings
├── requirements.txt               # Pinned dependencies
└── README.md                      # Setup and usage instructions
```

## Component Design

### 1. Core Services

#### 1.1 Tool Registry (`core/registry.py`)

The registry provides a centralized mechanism for tool registration, validation, and discovery. All tools register themselves at module import time, allowing the application to dynamically discover available analysis capabilities.

**Interface:**

```python
from dataclasses import dataclass
from typing import Callable, List, Literal

InputType = Literal["image", "text", "csv"]
ToolStatus = Literal["loaded", "fallback", "demo"]

@dataclass
class ToolMetadata:
    """Metadata describing a registered tool."""
    name: str
    display_name: str
    module_number: str  # "01", "02", "03", "04"
    description: str
    accepted_input_types: List[InputType]
    analyze_fn: Callable
    status: ToolStatus
    status_message: str = ""

class ToolRegistry:
    """Central registry for analysis tools."""
    
    def register(
        self,
        name: str,
        display_name: str,
        module_number: str,
        description: str,
        accepted_input_types: List[InputType],
        analyze_fn: Callable,
        status: ToolStatus = "demo",
        status_message: str = ""
    ) -> None:
        """Register a tool with the registry."""
        
    def get_tool(self, name: str) -> ToolMetadata:
        """Retrieve a tool by name."""
        
    def get_tools_by_input_type(self, input_type: InputType) -> List[ToolMetadata]:
        """Retrieve all tools accepting a specific input type."""
        
    def list_all_tools(self) -> List[ToolMetadata]:
        """List all registered tools."""
        
    def get_tool_status(self, name: str) -> tuple[ToolStatus, str]:
        """Get the current status and message for a tool."""

# Global registry instance
registry = ToolRegistry()
```

**Registration Pattern:**

Each tool registers itself in its `__init__.py`:

```python
# tools/deepfake/__init__.py
from core.registry import registry
from .analyzer import analyze_image

registry.register(
    name="deepfake",
    display_name="Deepfake Analyzer",
    module_number="01",
    description="Check whether an image is real or fake (AI-generated or manipulated).",
    accepted_input_types=["image"],
    analyze_fn=analyze_image,
    status="demo",
    status_message="Using stub implementation - demo results only"
)
```

#### 1.2 Result Schema (`core/schema.py`)

A standardized result structure ensures consistent interpretation across all tools and enables generic result rendering, export, and analysis.

```python
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

@dataclass
class AnalysisResult:
    """Standardized result structure for all analysis tools."""
    
    # Core fields
    label: str                    # Primary classification label
    score: float                  # Confidence score [0, 1]
    
    # Metadata
    model_name: str
    model_version: str
    is_demo: bool                 # True for stub implementations
    
    # Optional details
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate score is in valid range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be in range [0, 1], got {self.score}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return asdict(self)
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary optimized for display."""
        return {
            "Label": self.label,
            "Confidence": f"{self.score:.1%}",
            "Model": f"{self.model_name} v{self.model_version}",
            "Demo Mode": "Yes" if self.is_demo else "No",
            **self.details
        }
```

**Score Interpretation:**
- `0.0 - 0.3`: Low confidence in positive detection
- `0.3 - 0.7`: Uncertain / borderline
- `0.7 - 1.0`: High confidence in positive detection

The exact interpretation depends on the tool; for example:
- Deepfake: score = P(fake)
- Sentiment: score = strength of detected sentiment
- Fraud: score = P(fraudulent)
- Propaganda: score = P(propaganda)

#### 1.3 Input Readers (`core/readers.py`)

Input readers safely extract content from various sources while enforcing security constraints to prevent SSRF attacks, path traversal, and resource exhaustion.

```python
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image
import io

class InputReader:
    """Secure input reading with validation."""
    
    # Configuration
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    URL_TIMEOUT = 10  # seconds
    MAX_URL_SIZE = 5 * 1024 * 1024  # 5 MB
    
    # Private IP ranges (RFC 1918, RFC 4193, etc.)
    BLOCKED_IP_RANGES = [
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "::1/128",
        "fe80::/10",
        "fc00::/7"
    ]
    
    @staticmethod
    def read_image(file_data: bytes, filename: str) -> Image.Image:
        """Read and validate an image file."""
        
    @staticmethod
    def read_text_file(file_data: bytes, filename: str) -> str:
        """Read text from txt file with encoding detection."""
        
    @staticmethod
    def read_docx(file_data: bytes) -> Tuple[str, List[Image.Image]]:
        """Extract text and images from docx file."""
        
    @staticmethod
    def read_csv(file_data: bytes) -> Tuple[List[str], Optional[str]]:
        """Parse CSV and auto-detect text column."""
        
    @staticmethod
    def fetch_url(url: str) -> Tuple[Optional[Image.Image], Optional[str]]:
        """Fetch content from URL with security validation."""
        
    @staticmethod
    def _validate_url_scheme(url: str) -> None:
        """Ensure URL uses http or https only."""
        
    @staticmethod
    def _validate_url_host(url: str) -> None:
        """Prevent SSRF by blocking private/loopback/link-local IPs."""
        
    @staticmethod
    def _detect_csv_text_column(df) -> str:
        """Auto-detect the most likely text column in a CSV."""
```

**Security Features:**

1. **URL Scheme Validation**: Only `http://` and `https://` schemes are permitted. Schemes like `file://`, `ftp://`, or `data://` are rejected.

2. **SSRF Protection**: Before fetching any URL, the hostname is resolved and checked against blocked IP ranges:
   - Private addresses (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
   - Loopback addresses (127.0.0.0/8, ::1)
   - Link-local addresses (169.254.0.0/16, fe80::/10)

3. **Resource Limits**: Timeouts and size limits prevent resource exhaustion attacks.

4. **Encoding Safety**: All text is read with `errors="replace"` to handle malformed encoding gracefully.

#### 1.4 Settings Management (`core/settings.py`)

Configuration is loaded from `config.yaml` and environment variables (via `.env`). Settings are immutable after load to prevent accidental modification during runtime.

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml
from dotenv import load_dotenv
import os

@dataclass(frozen=True)
class Settings:
    """Application configuration."""
    
    # File handling
    max_file_size_mb: int = 10
    max_texts_per_batch: int = 500
    
    # URL fetching
    url_timeout_seconds: int = 10
    max_url_size_mb: int = 5
    
    # Models
    models_dir: Path = Path("models")
    
    # UI
    page_title: str = "GumShoo - Social Media Safety Detector"
    page_layout: str = "centered"
    
    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Settings":
        """Load settings from YAML and environment variables."""
        load_dotenv()
        
        if Path(config_path).exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}
        
        return cls(**config)

# Global settings instance
settings = Settings.load()
```

**config.yaml Example:**

```yaml
# Application settings
max_file_size_mb: 10
max_texts_per_batch: 500
url_timeout_seconds: 10
max_url_size_mb: 5

# UI configuration
page_title: "GumShoo - Social Media Safety Detector"
page_layout: "centered"

# Paths
models_dir: "models"
```

**.env Example:**

```bash
# No secrets required for stub implementation
# Future: API keys for cloud models
# OPENAI_API_KEY=sk-...
```

#### 1.5 Navigation (`core/navigation.py`)

Streamlit's multi-page architecture requires explicit state management and navigation control. This module provides utilities for consistent navigation.

```python
import streamlit as st
from typing import Any, Dict

def init_session_state(**defaults: Dict[str, Any]) -> None:
    """Initialize session state with default values."""
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def navigate_to_input(tool_name: str) -> None:
    """Navigate to input page with selected tool."""
    st.session_state.selected_tool = tool_name
    st.session_state.analysis_complete = False
    st.switch_page("pages/1_Input.py")

def navigate_to_results(result: Any) -> None:
    """Navigate to results page with analysis result."""
    st.session_state.result = result
    st.session_state.analysis_complete = True
    st.switch_page("pages/2_Results.py")

def navigate_to_home() -> None:
    """Navigate back to home page."""
    st.session_state.analysis_complete = False
    st.switch_page("app/Home.py")
```

### 2. Tool Plugin System

#### 2.1 Tool Interface

All tools implement a consistent interface:

```python
from core.schema import AnalysisResult
from PIL import Image
from typing import Union, List

def analyze(input_data: Union[Image.Image, str, List[str]]) -> Union[AnalysisResult, List[AnalysisResult]]:
    """
    Analyze input and return standardized result(s).
    
    Args:
        input_data: Image, single text, or list of texts
        
    Returns:
        Single result for image/single text, list of results for batch text
    """
```

#### 2.2 Stub Tool Implementation Pattern

Each stub tool follows this pattern:

```python
# tools/deepfake/analyzer.py
from core.schema import AnalysisResult
from PIL import Image
import hashlib

def analyze_image(image: Image.Image) -> AnalysisResult:
    """
    Stub implementation of deepfake detection.
    Returns demo results clearly marked as non-production.
    """
    # Generate deterministic fake score for demo purposes
    image_bytes = image.tobytes()
    hash_value = int(hashlib.md5(image_bytes).hexdigest(), 16)
    fake_score = (hash_value % 100) / 100.0
    
    label = "Fake" if fake_score >= 0.5 else "Real"
    
    return AnalysisResult(
        label=label,
        score=fake_score,
        model_name="Xception Ensemble (Stub)",
        model_version="0.0.1-demo",
        is_demo=True,
        details={
            "verdict": label,
            "confidence": fake_score,
            "analysis": "This is a demo result using deterministic fake data"
        },
        warnings=[
            "DEMO MODE: This result is generated from a stub implementation",
            "Real deepfake detection requires trained models"
        ]
    )
```

**Stub Tools:**

1. **Deepfake Analyzer** (`tools/deepfake/analyzer.py`)
   - Accepts: PIL Image
   - Returns: "Real" or "Fake" with fake probability
   - Demo logic: Hash image bytes to generate deterministic score

2. **Sentiment Analysis** (`tools/sentiment/analyzer.py`)
   - Accepts: Single text or list of texts
   - Returns: "Positive", "Neutral", or "Negative"
   - Demo logic: Hash text to select sentiment deterministically

3. **Fraud Detection** (`tools/fraud/detector.py`)
   - Accepts: Single text (ad/message)
   - Returns: "Fraud" or "Legit" with fraud probability
   - Demo logic: Simple keyword matching + hash-based score

4. **Propaganda Detection** (`tools/propaganda/detector.py`)
   - Accepts: Single text
   - Returns: "Propaganda" or "Not Propaganda" with score
   - Demo logic: Hash-based score generation

### 3. Application Pages

#### 3.1 Welcome Page (`app/Home.py`)

The landing page displays four tool cards in a grid layout, allowing analysts to select their analysis tool.

```python
import streamlit as st
from core.registry import registry
from core.navigation import init_session_state, navigate_to_input

st.set_page_config(
    page_title="GumShoo - Social Media Safety Detector",
    layout="centered"
)

# Load custom CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_session_state(
    selected_tool=None,
    analysis_complete=False,
    result=None
)

# Header
st.markdown('<div class="topbar"><span>Social Media Safety Detection</span><b>GumShoo</b></div>', 
            unsafe_allow_html=True)

st.title("Analysis Tools")

st.markdown("Select a detection module to analyze social media content for risk.")

# Tool cards in 2x2 grid
tools = registry.list_all_tools()

col1, col2 = st.columns(2)

for idx, tool in enumerate(tools):
    col = col1 if idx % 2 == 0 else col2
    
    with col:
        st.markdown(f'<div class="eyebrow">Module {tool.module_number}</div>', 
                   unsafe_allow_html=True)
        
        if st.button(
            tool.display_name,
            key=f"tool_{tool.name}",
            use_container_width=True
        ):
            navigate_to_input(tool.name)
        
        st.caption(tool.description)
        
        # Status indicator
        status_icon = {
            "loaded": "🟢",
            "fallback": "🟡", 
            "demo": "🔵"
        }.get(tool.status, "⚪")
        
        # Note: Remove emoji in production; use text only
        status_text = {
            "loaded": "Loaded",
            "fallback": "Fallback",
            "demo": "Demo Mode"
        }[tool.status]
        
        st.caption(f"Status: {status_text}")

# Footer notice
st.divider()
st.caption(
    "Notice: All analysis results are estimates, not verdicts. "
    "Results indicate probability and should be interpreted with appropriate "
    "context and domain expertise."
)
```

#### 3.2 Input Page (`pages/1_Input.py`)

A shared input collection page that adapts to the selected tool's accepted input types.

```python
import streamlit as st
from core.registry import registry
from core.readers import InputReader
from core.navigation import navigate_to_results, navigate_to_home
from typing import List

st.set_page_config(page_title="Input - GumShoo", layout="centered")

# Load custom CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "selected_tool" not in st.session_state or st.session_state.selected_tool is None:
    st.error("No tool selected. Please return to home page.")
    if st.button("Go to Home"):
        navigate_to_home()
    st.stop()

tool_name = st.session_state.selected_tool
tool = registry.get_tool(tool_name)

# Header
st.markdown('<div class="topbar"><span>Input Collection</span><b>GumShoo</b></div>',
            unsafe_allow_html=True)

st.title(f"Input: {tool.display_name}")
st.caption(tool.description)

# Input method selection
input_method = st.radio(
    "Input method:",
    ["Upload File", "Paste Text", "Enter URL"],
    horizontal=True
)

reader = InputReader()
input_data = None
error_message = None

try:
    if input_method == "Upload File":
        accepted_extensions = []
        if "image" in tool.accepted_input_types:
            accepted_extensions.extend(["png", "jpg", "jpeg", "webp"])
        if "text" in tool.accepted_input_types:
            accepted_extensions.extend(["txt", "docx"])
        if "csv" in tool.accepted_input_types:
            accepted_extensions.append("csv")
        
        uploaded_file = st.file_uploader(
            f"Upload file ({', '.join(accepted_extensions)})",
            type=accepted_extensions
        )
        
        if uploaded_file:
            file_data = uploaded_file.read()
            
            if len(file_data) > reader.MAX_FILE_SIZE:
                error_message = f"File size exceeds limit of {reader.MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
            else:
                filename = uploaded_file.name.lower()
                
                if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                    input_data = reader.read_image(file_data, filename)
                elif filename.endswith(".txt"):
                    input_data = reader.read_text_file(file_data, filename)
                elif filename.endswith(".docx"):
                    text, images = reader.read_docx(file_data)
                    # Use text for text tools, first image for image tools
                    if "image" in tool.accepted_input_types and images:
                        input_data = images[0]
                    elif "text" in tool.accepted_input_types:
                        input_data = text
                elif filename.endswith(".csv"):
                    texts, column_name = reader.read_csv(file_data)
                    input_data = texts
                    st.info(f"Detected text column: {column_name}")
    
    elif input_method == "Paste Text":
        if "text" not in tool.accepted_input_types:
            st.warning("This tool does not accept text input.")
        else:
            text_input = st.text_area("Paste text here:", height=200)
            
            if text_input:
                # Processing mode for text tools
                process_mode = st.radio(
                    "Process as:",
                    ["One whole document", "Separate posts (one per line)"],
                    horizontal=True
                )
                
                if process_mode == "Separate posts (one per line)":
                    input_data = [line.strip() for line in text_input.split("\n") if line.strip()]
                else:
                    input_data = text_input
    
    elif input_method == "Enter URL":
        url_input = st.text_input("Enter URL:")
        
        if url_input:
            with st.spinner("Fetching content..."):
                image, text = reader.fetch_url(url_input)
                
                if "image" in tool.accepted_input_types and image:
                    input_data = image
                elif "text" in tool.accepted_input_types and text:
                    input_data = text
                else:
                    error_message = "Could not extract compatible content from URL"

except Exception as e:
    error_message = f"Error reading input: {str(e)}"

if error_message:
    st.error(error_message)

# Analysis button
if input_data is not None:
    if st.button("Analyze", type="primary"):
        with st.spinner("Analyzing..."):
            try:
                result = tool.analyze_fn(input_data)
                navigate_to_results(result)
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

# Back button
if st.button("Back to Home"):
    navigate_to_home()
```

#### 3.3 Results Page (`pages/2_Results.py`)

Displays analysis results with tool-specific rendering, disclaimers, and export options.

```python
import streamlit as st
import pandas as pd
import json
from core.navigation import navigate_to_home, navigate_to_input
from typing import List

st.set_page_config(page_title="Results - GumShoo", layout="centered")

# Load custom CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "result" not in st.session_state or st.session_state.result is None:
    st.error("No results to display.")
    if st.button("Go to Home"):
        navigate_to_home()
    st.stop()

result = st.session_state.result

# Handle both single result and list of results
results = [result] if not isinstance(result, list) else result

# Header
st.markdown('<div class="topbar"><span>Analysis Results</span><b>GumShoo</b></div>',
            unsafe_allow_html=True)

st.title("Analysis Results")

# Prominent disclaimer
st.warning(
    "These results are estimates, not verdicts. "
    "They indicate probability and should be interpreted with appropriate "
    "context, domain expertise, and additional verification."
)

# Demo mode indicator
if results[0].is_demo:
    st.info(
        "DEMO MODE: These results are generated from stub implementations. "
        "Real analysis requires trained models."
    )

# Results display
if len(results) == 1:
    # Single result
    r = results[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Classification", r.label)
    with col2:
        st.metric("Confidence", f"{r.score:.1%}")
    with col3:
        st.metric("Model", f"{r.model_name}")
    
    st.subheader("Details")
    
    if r.details:
        for key, value in r.details.items():
            st.text(f"{key}: {value}")
    
    if r.warnings:
        st.subheader("Warnings")
        for warning in r.warnings:
            st.warning(warning)

else:
    # Multiple results (batch processing)
    st.subheader(f"Processed {len(results)} items")
    
    # Convert to DataFrame for display
    df_data = []
    for idx, r in enumerate(results):
        row = {
            "Index": idx + 1,
            "Label": r.label,
            "Confidence": f"{r.score:.1%}",
            "Model": r.model_name
        }
        df_data.append(row)
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)

# Export options
st.divider()
st.subheader("Export Results")

col1, col2 = st.columns(2)

with col1:
    # CSV export
    if len(results) > 0:
        csv_data = []
        for r in results:
            csv_data.append(r.to_display_dict())
        
        csv_df = pd.DataFrame(csv_data)
        csv_string = csv_df.to_csv(index=False)
        
        st.download_button(
            "Download CSV",
            csv_string,
            "gumshoo_results.csv",
            "text/csv"
        )

with col2:
    # JSON export
    json_data = [r.to_dict() for r in results]
    json_string = json.dumps(json_data, indent=2)
    
    st.download_button(
        "Download JSON",
        json_string,
        "gumshoo_results.json",
        "application/json"
    )

# Navigation
st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button("Analyze Another"):
        navigate_to_input(st.session_state.selected_tool)

with col2:
    if st.button("Back to Home"):
        navigate_to_home()
```

### 4. Theme and Visual Design

#### 4.1 Color Palette

Based on the legacy implementation, the professional theme uses:

- **Ink**: `#2A2540` - Primary text, headings
- **Muted**: `#6F6890` - Secondary text, captions
- **Line**: `#D9D1EC` - Borders, dividers
- **Plum**: `#5B4B8A` - Accent color
- **Lavender**: `#FBFAFE` - Light background
- **Soft Pink**: `#F5E6F1` - Alternative accent
- **Soft Green**: `#E8F5E9` - Success states

#### 4.2 Typography

- **Headings**: Source Serif 4 (weights: 500, 600)
- **Body**: Inter (weights: 400, 500, 600)
- **Code**: System monospace

#### 4.3 CSS Stylesheet (`assets/style.css`)

```css
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@500;600&display=swap");

:root {
  --ink: #2A2540;
  --muted: #6F6890;
  --line: #D9D1EC;
  --plum: #5B4B8A;
  --lavender: #FBFAFE;
}

/* Page container */
.block-container {
  max-width: 900px;
  padding-top: 1.6rem;
  padding-bottom: 4rem;
}

/* Hide Streamlit branding */
#MainMenu, footer {
  visibility: hidden;
}

header[data-testid="stHeader"] {
  background: transparent;
}

/* Top navigation bar */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.7rem;
  margin-bottom: 1.8rem;
  border-bottom: 1px solid var(--line);
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--muted);
}

.topbar b {
  color: var(--ink);
  font-weight: 600;
}

/* Module number eyebrow */
.eyebrow {
  font-size: 0.68rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #8A7FB0;
  font-weight: 600;
  margin-bottom: 0.1rem;
}

/* Typography */
h1 {
  font-family: "Source Serif 4", Georgia, serif;
  letter-spacing: -0.01em;
}

h2, h3 {
  font-family: "Source Serif 4", Georgia, serif;
  letter-spacing: -0.005em;
}

body, p, div {
  font-family: "Inter", -apple-system, sans-serif;
}

[data-testid="stMetricValue"] {
  font-family: "Source Serif 4", Georgia, serif;
}

[data-testid="stMetricLabel"] {
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 0.72rem;
}

hr {
  border-color: var(--line);
}

/* Buttons */
.stButton > button {
  font-weight: 500;
  letter-spacing: 0.02em;
  padding: 0.45rem 1.4rem;
  border-radius: 0.3rem;
}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
  background: var(--lavender);
  border: 1px dashed #BDB2DE;
  border-radius: 0.5rem;
}

/* Ensure WCAG AA contrast */
.stAlert {
  font-weight: 500;
}
```

#### 4.4 Streamlit Theme (`assets/.streamlit/config.toml`)

```toml
[theme]
primaryColor = "#5B4B8A"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#FBFAFE"
textColor = "#2A2540"
font = "sans serif"

[server]
headless = true
```

### 5. Data Flow

#### 5.1 Analysis Workflow

```
User → Welcome Page → Select Tool
                      ↓
              Input Page → Validate input type
                      ↓
              Read Input → InputReader (with security checks)
                      ↓
              Tool Registry → Get analyze function
                      ↓
              Execute Analysis → Stub tool (demo result)
                      ↓
              Results Page → Display + Export options
```

#### 5.2 Data Privacy

All data processing occurs in memory:

1. **No Disk Persistence**: Uploaded files are read into memory only. No temporary files are written.

2. **No Logging**: User content is never written to application logs. Only metadata (file size, type) may be logged.

3. **Memory Cleanup**: After analysis completes and results are displayed, input data is discarded from memory when the user navigates away.

4. **Session Isolation**: Streamlit session state is per-user and cleared when the session ends.

### 6. Error Handling

#### 6.1 Error Categories

1. **Input Validation Errors**: Invalid file types, oversized files, unsupported formats
2. **Security Errors**: Blocked URLs (SSRF protection), invalid schemes
3. **Processing Errors**: Encoding issues, malformed files, parsing failures
4. **Analysis Errors**: Exceptions during tool execution
5. **Configuration Errors**: Missing config files, invalid settings

#### 6.2 Error Handling Strategy

```python
# Example error handling pattern
try:
    # Attempt operation
    result = risky_operation()
except ValidationError as e:
    # User-facing error with guidance
    st.error(f"Invalid input: {e}. Please check your input and try again.")
except SecurityError as e:
    # Security error with explanation
    st.error(f"Security check failed: {e}")
except Exception as e:
    # Unexpected error with graceful degradation
    st.error(f"An unexpected error occurred: {e}")
    # Log full traceback for debugging (but not user content)
    logger.exception("Unexpected error during analysis")
```

**Principles:**

- Never expose internal implementation details in error messages
- Provide actionable guidance for user-correctable errors
- Log detailed errors server-side for debugging
- Always allow the user to retry with different input
- Never crash the application; always gracefully degrade

## Testing Strategy

### Test Categories

1. **Unit Tests** (pytest)
   - Input readers (file parsing, URL validation, SSRF protection)
   - Result schema (validation, serialization)
   - Tool registry (registration, discovery)
   - Settings loading

2. **Integration Tests**
   - End-to-end workflows (upload → analyze → display)
   - Tool registration and invocation
   - Multi-format input handling

3. **Property-Based Tests**
   - File format parsing (various valid/invalid inputs)
   - URL validation (comprehensive scheme/host testing)
   - Score validation (ensure all scores in [0, 1])

4. **Code Quality**
   - Ruff linting (zero violations)
   - Type checking with mypy
   - Docstring coverage

### Test Structure

```
tests/
├── test_registry.py         # Tool registry tests
├── test_schema.py           # Result schema validation
├── test_readers.py          # Input reader security + parsing
├── test_tools.py            # Stub tool behavior
└── test_integration.py      # End-to-end workflows
```

## Deployment

### Prerequisites

- Python 3.12+
- Windows PowerShell
- 10 MB free disk space (no models in foundation)

### Setup Instructions

```powershell
# Clone/navigate to project
cd d:\GumShoo

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run application
streamlit run app/Home.py
```

### Requirements (`requirements.txt`)

```
# Core
streamlit==1.29.0
python-dotenv==1.0.0
pyyaml==6.0.1

# Data processing
pandas==2.1.4
numpy==1.26.2

# Image handling
Pillow==10.1.0

# HTTP requests
requests==2.31.0

# Document parsing
python-docx==1.1.0

# Testing
pytest==7.4.3
pytest-cov==4.1.0

# Code quality
ruff==0.1.8
mypy==1.7.1

# Future: Real model dependencies
# torch==2.1.1
# timm==0.9.12
# transformers==4.36.1
# scikit-learn==1.3.2
# vaderSentiment==3.3.2
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: UI Content Excludes Emoji

*For any* text displayed on the Welcome Page, Input Page, or Results Page, the text SHALL NOT contain characters in Unicode emoji ranges (U+1F300–U+1F9FF, U+2600–U+26FF, etc.)

**Validates: Requirements 1.3, 7.8**

### Property 2: Valid File Extensions Accepted

*For any* uploaded file with extension in {png, jpg, jpeg, webp, docx, txt, csv}, the Input Page SHALL accept the file without displaying an error message

**Validates: Requirements 2.2**

### Property 3: Invalid File Extensions Rejected

*For any* uploaded file with extension NOT in {png, jpg, jpeg, webp, docx, txt, csv}, the Input Page SHALL reject the file and display a clear error message

**Validates: Requirements 2.3**

### Property 4: CSV Row Processing

*For any* valid CSV file with N rows, the Input Page SHALL process exactly N rows

**Validates: Requirements 2.6**

### Property 5: CSV Text Column Detection

*For any* CSV file containing at least one non-numeric column, the Input Reader SHALL successfully identify a text column for analysis

**Validates: Requirements 2.7**

### Property 6: Input-Tool Compatibility Validation

*For any* combination of input type and selected tool, the Input Page SHALL validate compatibility before invoking the analysis function

**Validates: Requirements 2.8, 14.4**

### Property 7: DOCX Text Extraction

*For any* valid DOCX file containing text content, the Input Reader SHALL extract all paragraph text

**Validates: Requirements 3.1**

### Property 8: DOCX Image Extraction

*For any* valid DOCX file containing embedded images, the Input Reader SHALL extract all extractable images

**Validates: Requirements 3.2**

### Property 9: Text File Reading

*For any* text file with valid or invalid UTF-8 encoding, the Input Reader SHALL successfully read the file content (replacing invalid bytes)

**Validates: Requirements 3.3, 3.12**

### Property 10: CSV Parsing

*For any* valid CSV file, the Input Reader SHALL successfully parse the file into rows and columns

**Validates: Requirements 3.4**

### Property 11: Valid URL Schemes Accepted

*For any* URL with scheme in {http, https}, the Input Reader SHALL attempt to fetch the content

**Validates: Requirements 3.5**

### Property 12: Invalid URL Schemes Rejected

*For any* URL with scheme NOT in {http, https}, the Input Reader SHALL reject the request with an error message before attempting to fetch

**Validates: Requirements 3.6**

### Property 13: Private IP Address Blocking

*For any* URL that resolves to an IP address in private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), the Input Reader SHALL reject the request with an error message

**Validates: Requirements 3.9**

### Property 14: Loopback Address Blocking

*For any* URL that resolves to a loopback address (127.0.0.0/8, ::1), the Input Reader SHALL reject the request with an error message

**Validates: Requirements 3.10**

### Property 15: Link-Local Address Blocking

*For any* URL that resolves to a link-local address (169.254.0.0/16, fe80::/10), the Input Reader SHALL reject the request with an error message

**Validates: Requirements 3.11**

### Property 16: Tool Registration Requires Name

*For any* tool registration attempt without a name field, the Tool Registry SHALL reject the registration

**Validates: Requirements 4.2**

### Property 17: Tool Registration Requires Input Types

*For any* tool registration attempt without accepted_input_types declared, the Tool Registry SHALL reject the registration

**Validates: Requirements 4.3**

### Property 18: Tool Registration Requires Analyze Function

*For any* tool registration attempt without an analyze function, the Tool Registry SHALL reject the registration

**Validates: Requirements 4.4**

### Property 19: Tool Discovery by Name

*For any* registered tool with name N, calling get_tool(N) SHALL return the tool's metadata

**Validates: Requirements 4.5**

### Property 20: Tool Discovery by Input Type

*For any* registered tool accepting input type T, the tool SHALL appear in the results of get_tools_by_input_type(T)

**Validates: Requirements 4.6**

### Property 21: Result Score Constraint

*For any* AnalysisResult instance, the score field SHALL be in the range [0.0, 1.0] inclusive

**Validates: Requirements 5.8**

### Property 22: Result Field Display

*For any* AnalysisResult displayed on the Results Page, all fields (label, score, details, warnings, model_name, model_version, is_demo) SHALL be visible in the rendered output

**Validates: Requirements 6.6-6.12**

### Property 23: Tool Status Display

*For any* registered tool, the Status Panel SHALL display the tool's current status (loaded, fallback, or demo)

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 24: No File Persistence

*For any* file uploaded by a user, no file SHALL be written to disk during or after processing

**Validates: Requirements 9.1, 9.3**

### Property 25: No Content Logging

*For any* user-provided content (text, image data, file contents), that content SHALL NOT appear in application logs

**Validates: Requirements 9.2**

### Property 26: Invalid Input Error Messages

*For any* input validation failure, the Input Page SHALL display an error message describing the validation failure

**Validates: Requirements 14.1, 14.2, 14.3**

### Property 27: Analysis Error Handling

*For any* error occurring during tool analysis, the Application SHALL display an error message without terminating

**Validates: Requirements 15.1, 15.2**

### Property 28: Input Reader Error Recovery

*For any* error in the Input Reader, the Application SHALL display an error message and allow the user to retry with different input

**Validates: Requirements 15.3, 15.4**

## Future Extensions

This foundation is designed for extension:

1. **Real Model Integration**: Replace stub implementations with trained models by updating the analyze function in each tool package

2. **Additional Tools**: Add new tools by creating a new package in `tools/` and registering via the registry

3. **Advanced Input Types**: Extend InputReader to support additional formats (PDF, audio, video)

4. **Batch Processing**: Enhance input handling for large-scale batch analysis

5. **Result History**: Add database layer to persist analysis history

6. **User Authentication**: Add user accounts and role-based access control

7. **API Layer**: Expose analysis tools via REST API for integration with other systems

8. **Model Performance Monitoring**: Track model accuracy, latency, and resource usage

## Conclusion

This design provides a solid, extensible foundation for GumShoo. The plugin architecture allows independent development of each detection tool. The security-focused input handling prevents common vulnerabilities. The standardized result schema enables consistent user experience and future analytics. The stub implementations validate all integration points without requiring trained models.

The next phase will involve implementing this design, followed by integration of real detection models as they become available.
