"""
Deepfake Analyzer Tool

Real AI-based deepfake detection using trained Xception ensemble models.
"""

from core.registry import registry
from .analyzer import analyze_image, _model_available, _model_error

# Register tool at module import time with actual model status
status = "loaded" if _model_available else "fallback"
status_msg = "Xception ensemble models ready" if _model_available else f"Model error: {_model_error}"

registry.register(
    name="deepfake",
    display_name="Deepfake Analyzer", 
    module_number="01",
    description="Check whether an image is real or fake using trained AI models.",
    accepted_input_types=["image"],
    analyze_fn=analyze_image,
    status=status,
    status_message=status_msg
)

__all__ = ["analyze_image"]
