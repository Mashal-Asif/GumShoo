"""
Propaganda Detection Detector

Stub implementation that generates deterministic demo results
based on content hash and simple heuristics. Does not use real ML models.
"""

import hashlib
import re

from core.schema import AnalysisResult


# Simple propaganda technique indicators for demo purposes
PROPAGANDA_PATTERNS = [
    ("Loaded language", r"(evil|corrupt|betrayal|destroy|attack|threat|enemy)"),
    ("Appeal to fear", r"(danger|threat|risk|unsafe|disaster|catastrophe)"),
    ("Name calling", r"(traitor|liar|criminal|corrupt|fake|fraud)"),
    ("Glittering generalities", r"(freedom|justice|truth|honor|patriot|hero)"),
    ("Appeal to authority", r"(expert|study|research|scientist|professor)"),
    ("Bandwagon", r"(everyone|everybody|all of us|join us|together)"),
    ("Repetition", r"(\w+)\s+\1"),  # Word repetition
]


def detect_propaganda(text: str) -> AnalysisResult:
    """
    Analyze text for propaganda techniques (stub implementation).
    
    Uses simple pattern matching combined with hash-based scoring
    to generate deterministic demo results. This is a stub and does
    not perform real propaganda detection.
    
    Args:
        text: Text content to analyze for propaganda techniques
    
    Returns:
        AnalysisResult with demo propaganda analysis
    
    Example:
        >>> result = detect_propaganda("This is a test message.")
        >>> result.is_demo
        True
        >>> result.label in ["Propaganda", "Not Propaganda"]
        True
    """
    text_lower = text.lower()
    
    # Detect techniques
    techniques_found = []
    for technique_name, pattern in PROPAGANDA_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            techniques_found.append(technique_name)
    
    # Base score on detected techniques
    technique_score = min(0.9, len(techniques_found) * 0.2)
    
    # Add hash-based variation
    hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
    hash_score = (hash_value % 70) / 100.0
    
    # Combine scores
    propaganda_score = max(technique_score, hash_score)
    
    # Determine label
    if propaganda_score >= 0.5:
        label = "Propaganda"
        verdict = "This content shows characteristics of propaganda or manipulative messaging"
    else:
        label = "Not Propaganda"
        verdict = "This content appears to be straightforward messaging"
    
    return AnalysisResult(
        label=label,
        score=propaganda_score,
        model_name="Propaganda Detector (Stub)",
        model_version="0.0.1-demo",
        is_demo=True,
        details={
            "verdict": verdict,
            "confidence": f"{propaganda_score:.1%}",
            "techniques_detected": len(techniques_found),
            "techniques": techniques_found if techniques_found else ["No obvious propaganda techniques detected"],
            "text_length": len(text),
            "analysis": "Demo result using pattern matching and hash-based scoring"
        },
        warnings=[
            "DEMO MODE: This result is generated from a stub implementation",
            "Real propaganda detection requires trained transformer models and linguistic analysis",
            "Technique detection is based on simple pattern matching"
        ]
    )
