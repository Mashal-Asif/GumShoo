"""
GumShoo Results Page

Displays analysis results with appropriate disclaimers and export options.
Handles both single results and batch results.
"""

import json
import pathlib
import streamlit as st
import pandas as pd
from typing import List, Union

from core.navigation import navigate_to_home, navigate_to_input
from core.schema import AnalysisResult
from core.settings import settings


def load_css() -> None:
    """Load custom CSS stylesheet."""
    css_path = pathlib.Path(__file__).parent.parent.parent / 'assets' / 'style.css'
    with open(css_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def render_topbar() -> None:
    """Render the top navigation bar."""
    st.markdown(
        '<div class="topbar-nav">'
        '<span>Analysis Results</span>'
        '<b>GumShoo</b>'
        '</div>',
        unsafe_allow_html=True
    )


def render_single_result(result: AnalysisResult) -> None:
    """Render a single analysis result."""
    # Main metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Classification", result.label)
    
    with col2:
        confidence_color = "green" if result.score >= 0.7 else "orange" if result.score >= 0.4 else "red"
        st.metric("Confidence", f"{result.score:.1%}")
    
    with col3:
        st.metric("Model", result.model_name)
        st.caption(f"Version {result.model_version}")
    
    # Additional details
    if result.details:
        st.markdown("### Analysis Details")
        
        # Display details in a structured way
        for key, value in result.details.items():
            if key in ["verdict", "analysis"]:
                st.markdown(f"**{key.title()}:** {value}")
            elif isinstance(value, (list, tuple)):
                st.markdown(f"**{key.replace('_', ' ').title()}:**")
                for item in value:
                    st.markdown(f"- {item}")
            else:
                st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
    
    # Warnings
    if result.warnings:
        st.markdown("### Important Notes")
        for warning in result.warnings:
            st.warning(warning)


def render_batch_results(results: List[AnalysisResult]) -> None:
    """Render batch analysis results."""
    st.markdown(f"### Batch Analysis Results ({len(results)} items)")
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    labels = [r.label for r in results]
    scores = [r.score for r in results]
    
    with col1:
        st.metric("Total Items", len(results))
    
    with col2:
        avg_confidence = sum(scores) / len(scores) if scores else 0
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    
    with col3:
        unique_labels = len(set(labels))
        st.metric("Unique Labels", unique_labels)
    
    with col4:
        high_conf_count = sum(1 for score in scores if score >= 0.7)
        st.metric("High Confidence", f"{high_conf_count}/{len(results)}")
    
    # Results table
    st.markdown("#### Detailed Results")
    
    # Prepare data for table
    table_data = []
    for i, result in enumerate(results):
        row = {
            "Item": i + 1,
            "Label": result.label,
            "Confidence": f"{result.score:.1%}",
            "Score": result.score,
            "Model": result.model_name,
            "Demo": "Yes" if result.is_demo else "No"
        }
        table_data.append(row)
    
    df = pd.DataFrame(table_data)
    
    # Display with formatting
    st.dataframe(
        df.drop("Score", axis=1),  # Hide raw score column
        use_container_width=True,
        hide_index=True
    )
    
    # Distribution chart
    if len(set(labels)) > 1:
        st.markdown("#### Label Distribution")
        label_counts = pd.Series(labels).value_counts()
        st.bar_chart(label_counts)


def create_export_data(results: Union[AnalysisResult, List[AnalysisResult]]) -> tuple[pd.DataFrame, List[dict]]:
    """Create export data for both CSV and JSON formats."""
    if isinstance(results, AnalysisResult):
        results = [results]
    
    # CSV data (display format)
    csv_data = []
    for i, result in enumerate(results):
        row = result.to_display_dict()
        row["Item"] = i + 1
        csv_data.append(row)
    
    csv_df = pd.DataFrame(csv_data)
    
    # JSON data (raw format)
    json_data = [result.to_dict() for result in results]
    
    return csv_df, json_data


def main() -> None:
    """Main results page logic."""
    # Configure page
    st.set_page_config(
        page_title="Results - GumShoo",
        layout=settings.page_layout,
        initial_sidebar_state="collapsed"
    )
    
    # Load custom CSS
    load_css()
    
    # Check if results exist
    if "result" not in st.session_state or st.session_state.result is None:
        st.error("No analysis results to display.")
        st.markdown("Please return to the home page and run an analysis.")
        if st.button("Go to Home", type="primary"):
            navigate_to_home()
        st.stop()
    
    # Render page header
    render_topbar()
    
    st.title("Analysis Results")
    
    # Prominent disclaimer
    st.error(
        "🚨 **Important Disclaimer:** These results are estimates, not definitive verdicts. "
        "They indicate probability based on machine learning analysis and should be "
        "interpreted by trained analysts as part of a comprehensive evaluation process."
    )
    
    # Get results (handle both single result and list)
    result_data = st.session_state.result
    is_batch = isinstance(result_data, list)
    results = result_data if is_batch else [result_data]
    
    # Demo mode warning
    if results[0].is_demo:
        st.info(
            "📍 **Demo Mode:** These results are generated from stub implementations "
            "for demonstration purposes. Real analysis requires trained machine learning models."
        )
    
    st.markdown("---")
    
    # Render results
    if is_batch:
        render_batch_results(results)
    else:
        render_single_result(results[0])
    
    # Export section
    st.markdown("---")
    st.markdown("### Export Results")
    
    csv_df, json_data = create_export_data(result_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        csv_string = csv_df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv_string,
            file_name="gumshoo_results.csv",
            mime="text/csv",
            help="Download results as CSV spreadsheet"
        )
    
    with col2:
        # JSON export
        json_string = json.dumps(json_data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📋 Download JSON",
            data=json_string,
            file_name="gumshoo_results.json",
            mime="application/json",
            help="Download results as JSON data"
        )
    
    # Show export preview
    with st.expander("Preview Export Data"):
        tab1, tab2 = st.tabs(["CSV Preview", "JSON Preview"])
        
        with tab1:
            st.dataframe(csv_df, use_container_width=True)
        
        with tab2:
            st.json(json_data)
    
    # Navigation section
    st.markdown("---")
    st.markdown("### What's Next?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Analyze Another", type="secondary", use_container_width=True):
            if "selected_tool" in st.session_state and st.session_state.selected_tool:
                navigate_to_input(st.session_state.selected_tool)
            else:
                navigate_to_home()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            navigate_to_home()
    
    # Technical details in expander
    with st.expander("Technical Details"):
        st.markdown("#### Analysis Metadata")
        sample_result = results[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Model Name:** {sample_result.model_name}")
            st.markdown(f"**Model Version:** {sample_result.model_version}")
            st.markdown(f"**Demo Mode:** {'Yes' if sample_result.is_demo else 'No'}")
        
        with col2:
            st.markdown(f"**Results Count:** {len(results)}")
            if len(results) > 1:
                avg_score = sum(r.score for r in results) / len(results)
                st.markdown(f"**Average Score:** {avg_score:.3f}")
        
        if sample_result.warnings:
            st.markdown("#### Warnings")
            for warning in sample_result.warnings:
                st.caption(f"⚠️ {warning}")


if __name__ == "__main__":
    main()