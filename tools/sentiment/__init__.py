"""
Sentiment Analysis Tool

Real sentiment analysis using VADER (Valence Aware Dictionary and sEntiment Reasoner).
Specifically tuned for social media text analysis.
"""

from core.registry import registry
from .analyzer import analyze_text, _model_available, _model_error

# Register tool at module import time with actual model status  
status = "loaded" if _model_available else "fallback"
status_msg = "VADER sentiment model ready" if _model_available else f"Model error: {_model_error}"

registry.register(
    name="sentiment", 
    display_name="Sentiment Analysis",
    module_number="02",
    description="Analyze the sentiment of posts, tweets or documents using VADER.",
    accepted_input_types=["text", "csv"],
    analyze_fn=analyze_text,
    status=status,
    status_message=status_msg
)

__all__ = ["analyze_text"]
