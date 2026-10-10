"""
GumShoo Input Page

Handles input collection for analysis tools.
Supports file upload, text paste, and URL input with validation.
"""

import pathlib
import streamlit as st
from typing import Any, List, Union
from PIL import Image

from core.navigation import navigate_to_results, navigate_to_home
from core.readers import InputReader, InputValidationError, SSRFProtectionError
from core.registry import registry
from core.settings import settings


def load_css() -> None:
    """Load custom CSS stylesheet."""
    css_path = pathlib.Path(__file__).parent.parent.parent / 'assets' / 'style.css'
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def render_topbar(tool_name: str) -> None:
    """Render the top navigation bar with tool context."""
    st.markdown(
        f'<div class="topbar-nav">'
        f'<span>Input Collection</span>'
        f'<b>GumShoo - {tool_name}</b>'
        f'</div>',
        unsafe_allow_html=True
    )


def get_accepted_extensions(tool) -> List[str]:
    """Get list of accepted file extensions for a tool."""
    extensions = []
    if "image" in tool.accepted_input_types:
        extensions.extend(["png", "jpg", "jpeg", "webp"])
    if "text" in tool.accepted_input_types:
        extensions.extend(["txt", "docx"])
    if "csv" in tool.accepted_input_types:
        extensions.append("csv")
    return extensions


def handle_file_upload(tool, reader: InputReader) -> Any:
    """Handle file upload input method."""
    extensions = get_accepted_extensions(tool)
    
    uploaded_file = st.file_uploader(
        f"Upload file ({', '.join(extensions)})",
        type=extensions,
        help=f"Maximum file size: {settings.max_file_size_mb} MB"
    )
    
    if uploaded_file is None:
        return None
    
    # Check file size
    file_data = uploaded_file.read()
    if len(file_data) > settings.max_file_size_bytes:
        st.error(
            f"File size ({len(file_data) / 1024 / 1024:.1f} MB) exceeds "
            f"the maximum limit of {settings.max_file_size_mb} MB."
        )
        return None
    
    filename = uploaded_file.name.lower()
    
    try:
        # Route based on file extension
        if filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
            if "image" not in tool.accepted_input_types:
                st.error("This tool does not accept image files.")
                return None
            return reader.read_image(file_data, filename)
            
        elif filename.endswith(".txt"):
            if "text" not in tool.accepted_input_types:
                st.error("This tool does not accept text files.")
                return None
            return reader.read_text_file(file_data, filename)
            
        elif filename.endswith(".docx"):
            text, images = reader.read_docx(file_data)
            # Route to appropriate handler based on tool capabilities
            if "image" in tool.accepted_input_types and images:
                st.info(f"Using first image from document (found {len(images)} images)")
                return images[0]
            elif "text" in tool.accepted_input_types and text.strip():
                st.info(f"Extracted text content ({len(text)} characters)")
                return text
            else:
                st.error("Could not extract compatible content from DOCX file.")
                return None
                
        elif filename.endswith(".csv"):
            if "csv" not in tool.accepted_input_types:
                st.error("This tool does not accept CSV files.")
                return None
            texts, column_name = reader.read_csv(file_data)
            st.info(f"Detected text column: '{column_name}' with {len(texts)} entries")
            return texts
            
        else:
            st.error(f"Unsupported file type: {filename}")
            return None
            
    except InputValidationError as e:
        st.error(f"File validation error: {e}")
        return None
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None


def handle_text_input(tool) -> Any:
    """Handle text paste input method."""
    if "text" not in tool.accepted_input_types:
        st.warning("This tool does not accept text input.")
        return None
    
    text_input = st.text_area(
        "Paste text here:",
        height=200,
        help="Enter the text content you want to analyze"
    )
    
    if not text_input.strip():
        return None
    
    # Processing mode selection
    process_mode = st.radio(
        "Process as:",
        ["One whole document", "Separate posts (one per line)"],
        horizontal=True,
        help="Choose how to split the text for analysis"
    )
    
    if process_mode == "Separate posts (one per line)":
        # Split by lines and filter empty lines
        texts = [line.strip() for line in text_input.split("\n") if line.strip()]
        if not texts:
            st.warning("No valid text lines found.")
            return None
        st.info(f"Processing {len(texts)} separate posts")
        return texts
    else:
        return text_input.strip()


def handle_url_input(tool, reader: InputReader) -> Any:
    """Handle URL input method."""
    url_input = st.text_input(
        "Enter URL:",
        help="Enter a URL to fetch content from (http:// or https:// only)"
    )
    
    if not url_input.strip():
        return None
    
    try:
        with st.spinner("Fetching content from URL..."):
            image, text = reader.fetch_url(url_input)
            
            # Route based on what was fetched and tool capabilities
            if image and "image" in tool.accepted_input_types:
                st.success("Successfully fetched image from URL")
                return image
            elif text and "text" in tool.accepted_input_types:
                st.success(f"Successfully fetched text from URL ({len(text)} characters)")
                return text
            else:
                available = ", ".join(tool.accepted_input_types)
                st.error(
                    f"Could not extract compatible content from URL. "
                    f"This tool accepts: {available}"
                )
                return None
                
    except SSRFProtectionError as e:
        st.error(f"URL blocked for security reasons: {e}")
        return None
    except InputValidationError as e:
        st.error(f"URL validation error: {e}")
        return None
    except Exception as e:
        st.error(f"Error fetching URL: {e}")
        return None


def perform_analysis(tool, input_data: Any) -> None:
    """Perform analysis and navigate to results."""
    try:
        with st.spinner("Analyzing content..."):
            result = tool.analyze_fn(input_data)
            navigate_to_results(result)
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.error("Please check your input and try again.")


def main() -> None:
    """Main input page logic."""
    # Configure page
    st.set_page_config(
        page_title="Input - GumShoo",
        layout=settings.page_layout,
        initial_sidebar_state="collapsed"
    )
    
    # Load custom CSS
    load_css()
    
    # Check if tool is selected
    if "selected_tool" not in st.session_state or st.session_state.selected_tool is None:
        st.error("No analysis tool selected. Please return to the home page to select a tool.")
        if st.button("Go to Home", type="primary"):
            navigate_to_home()
        st.stop()
    
    # Get tool information
    tool_name = st.session_state.selected_tool
    try:
        tool = registry.get_tool(tool_name)
    except KeyError:
        st.error(f"Unknown tool: {tool_name}")
        if st.button("Go to Home", type="primary"):
            navigate_to_home()
        st.stop()
    
    # Render page header
    render_topbar(tool.display_name)
    
    st.title(f"Input: {tool.display_name}")
    st.markdown(f"**Description:** {tool.description}")
    
    # Show accepted input types
    accepted_types = ", ".join(tool.accepted_input_types)
    st.markdown(f"**Accepts:** {accepted_types}")
    
    # Tool status indicator
    status_color = {"loaded": "green", "demo": "blue", "fallback": "orange"}.get(tool.status, "gray")
    st.markdown(f"**Status:** :{status_color}[{tool.status.title()}]")
    if tool.status_message:
        st.caption(tool.status_message)
    
    st.markdown("---")
    
    # Input method tabs
    tab1, tab2, tab3 = st.tabs(["📁 Upload File", "📝 Paste Text", "🔗 Enter URL"])
    
    reader = InputReader()
    input_data = None
    
    with tab1:
        st.markdown("### Upload File")
        input_data = handle_file_upload(tool, reader)
    
    with tab2:
        st.markdown("### Paste Text")
        text_data = handle_text_input(tool)
        if text_data is not None:
            input_data = text_data
    
    with tab3:
        st.markdown("### Enter URL")
        url_data = handle_url_input(tool, reader)
        if url_data is not None:
            input_data = url_data
    
    # Analysis section
    if input_data is not None:
        st.markdown("---")
        st.markdown("### Ready for Analysis")
        
        # Show preview of what will be analyzed
        if isinstance(input_data, Image.Image):
            st.image(input_data, caption="Image to analyze", use_column_width=True)
        elif isinstance(input_data, str):
            preview = input_data[:500] + "..." if len(input_data) > 500 else input_data
            st.text_area("Text to analyze:", preview, height=100, disabled=True)
        elif isinstance(input_data, list):
            st.info(f"Batch analysis: {len(input_data)} items")
            if input_data:
                preview = str(input_data[0])[:200] + "..." if len(str(input_data[0])) > 200 else str(input_data[0])
                st.text(f"First item preview: {preview}")
        
        # Analysis button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔍 Analyze", type="primary", use_container_width=True):
                perform_analysis(tool, input_data)
        with col2:
            st.caption("Click to run the analysis")
    
    # Navigation
    st.markdown("---")
    if st.button("← Back to Home"):
        navigate_to_home()


if __name__ == "__main__":
    main()