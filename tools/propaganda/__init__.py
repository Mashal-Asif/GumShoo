"""
Propaganda Detection Tool

Stub implementation for propaganda and manipulative content detection.
Returns demo results for architectural validation.
"""

from core.registry import registry
from .detector import detect_propaganda

# Register tool at module import time
registry.register(
    name="propaganda",
    display_name="Propaganda Detection",
    module_number="04",
    description="Detect propaganda and manipulative persuasion in text.",
    accepted_input_types=["text"],
    analyze_fn=detect_propaganda,
    status="demo",
    status_message="Using stub implementation - demo results only"
)

__all__ = ["detect_propaganda"]
