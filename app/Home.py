"""
GumShoo Home Page

Main entry point for the social media safety detection application.
Displays available analysis tools and allows users to select one for analysis.
"""

import pathlib
import streamlit as st

# Import all tool packages to trigger self-registration
import tools.deepfake
import tools.sentiment
import tools.fraud
import tools.propaganda

from core.navigation import init_session_state, navigate_to_input
from core.registry import registry
from core.settings import settings


def load_css() -> None:
    """Load custom CSS stylesheet."""
    css_path = pathlib.Path(__file__).parent.parent / 'assets' / 'style.css'
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def render_topbar() -> None:
    """Render the top navigation bar."""
    st.markdown(
        '<div class="topbar-nav"><h1>GumShoo - Social Media Safety Detector</h1></div>',
        unsafe_allow_html=True
    )


def render_tool_card(tool) -> None:
    """
    Render an individual tool card with selection button.
    
    Args:
        tool: ToolMetadata instance from the registry
    """
    # Create columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Module eyebrow
        st.markdown(
            f'<div class="module-eyebrow">Module {tool.module_number}</div>',
            unsafe_allow_html=True
        )
        
        # Tool title and description
        st.markdown(f'<h3>{tool.display_name}</h3>', unsafe_allow_html=True)
        st.markdown(f'<p>{tool.description}</p>', unsafe_allow_html=True)
        
        # Status indicator (no emoji)
        status_class = tool.status
        status_text = {
            "loaded": "Ready",
            "demo": "Demo Mode", 
            "fallback": "Fallback Mode"
        }.get(tool.status, tool.status.title())
        
        st.markdown(
            f'<div class="tool-status {status_class}">{status_text}</div>',
            unsafe_allow_html=True
        )
        
        if tool.status_message:
            st.caption(tool.status_message)
    
    with col2:
        # Selection button
        if st.button(f"Analyze", key=f"select_{tool.name}", use_container_width=True):
            navigate_to_input(tool.name)


def main() -> None:
    """Main application entry point."""
    # Configure page
    st.set_page_config(
        page_title=settings.page_title,
        layout=settings.page_layout,
        initial_sidebar_state="collapsed"
    )
    
    # Load custom CSS
    load_css()
    
    # Initialize session state
    init_session_state(
        selected_tool=None,
        analysis_complete=False,
        result=None
    )
    
    # Render topbar navigation
    render_topbar()
    
    # Welcome section
    st.markdown("""
    ## Welcome to GumShoo
    
    GumShoo analyzes social media content to help identify potential risks and safety concerns. 
    Select an analysis tool below to get started.
    
    **Important:** All analysis results are estimates based on machine learning models, 
    not definitive verdicts. Use these insights as part of a broader evaluation process.
    """)
    
    st.markdown("---")
    
    # Get all registered tools
    tools = registry.list_all_tools()
    
    if not tools:
        st.error("No analysis tools are available. Please check the configuration.")
        return
    
    # Display tools in 2x2 grid
    st.markdown("## Available Analysis Tools")
    
    # Create 2x2 grid layout
    col1, col2 = st.columns(2)
    
    for i, tool in enumerate(tools):
        with col1 if i % 2 == 0 else col2:
            with st.container():
                st.markdown('<div class="tool-card">', unsafe_allow_html=True)
                render_tool_card(tool)
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer disclaimer
    st.markdown("---")
    st.markdown(
        '<div class="footer">'
        'GumShoo provides analysis estimates, not definitive verdicts. '
        'Results should be interpreted by trained analysts and used as part of '
        'a comprehensive evaluation process.'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()