"""
Fraud Detection Tool

Real ML-based fraud detection using trained scikit-learn model.
Trained on SMS Spam Collection dataset with TF-IDF features.
"""

from core.registry import registry
from .detector import detect_fraud, _model_available, _model_error

# Register tool at module import time with actual model status
status = "loaded" if _model_available else "fallback"  
status_msg = "SMS fraud model ready" if _model_available else f"Model error: {_model_error}"

registry.register(
    name="fraud",
    display_name="Fraud Detection",
    module_number="03", 
    description="Detect scam or fraudulent ads, job offers and messages using trained ML.",
    accepted_input_types=["text"],
    analyze_fn=detect_fraud,
    status=status,
    status_message=status_msg
)

__all__ = ["detect_fraud"]
