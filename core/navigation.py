"""
Navigation Utilities Module

Provides helper functions for Streamlit session state management
and page navigation in the multi-page application.
"""

from typing import Any

import streamlit as st


def init_session_state(**defaults: Any) -> None:
    """
    Initialize session state with default values.
    
    Sets default values for session state keys if they don't already exist.
    This ensures consistent state initialization across pages.
    
    Args:
        **defaults: Key-value pairs to initialize in session state
    
    Example:
        >>> init_session_state(
        ...     selected_tool=None,
        ...     analysis_complete=False,
        ...     result=None
        ... )
    
    Note:
        Only sets values for keys that don't exist yet. Existing values
        are preserved to maintain state across page navigation.
    """
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate_to_input(tool_name: str) -> None:
    """
    Navigate to the input page with a selected tool.
    
    Sets the selected tool in session state and switches to the input page.
    Clears any previous analysis results.
    
    Args:
        tool_name: Unique identifier of the tool to analyze with
    
    Example:
        >>> navigate_to_input("deepfake")
    
    Note:
        This function uses Streamlit's switch_page which triggers a rerun.
        Code after this call will not execute.
    """
    st.session_state.selected_tool = tool_name
    st.session_state.analysis_complete = False
    st.session_state.result = None
    st.switch_page("pages/1_Input.py")


def navigate_to_results(result: Any) -> None:
    """
    Navigate to the results page with analysis results.
    
    Stores the analysis result in session state and switches to the results page.
    
    Args:
        result: Analysis result (AnalysisResult instance or list of results)
    
    Example:
        >>> from core.schema import AnalysisResult
        >>> result = AnalysisResult(
        ...     label="Fake",
        ...     score=0.85,
        ...     model_name="Xception",
        ...     model_version="1.0",
        ...     is_demo=True
        ... )
        >>> navigate_to_results(result)
    
    Note:
        This function uses Streamlit's switch_page which triggers a rerun.
        Code after this call will not execute.
    """
    st.session_state.result = result
    st.session_state.analysis_complete = True
    st.switch_page("pages/2_Results.py")


def navigate_to_home() -> None:
    """
    Navigate back to the home page.
    
    Clears analysis state and returns to the welcome page.
    
    Example:
        >>> navigate_to_home()
    
    Note:
        This function uses Streamlit's switch_page which triggers a rerun.
        Code after this call will not execute.
    """
    st.session_state.analysis_complete = False
    st.switch_page("app/Home.py")
